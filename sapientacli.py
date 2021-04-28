from typing import List
import websockets
import click
import asyncio
import json
import os
import logging
import aiohttp
import tqdm
import tqdm.asyncio

ENDPOINT = os.environ.get("SAPIENTA_ENDPOINT", "https://sapienta.papro.org.uk")

logger = logging.getLogger("sapientacli")


async def submit_job(file_path: str) -> dict:
    """Submit job for processing, return ID on queue"""

    data = {'file': open(file_path, 'rb')}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{ENDPOINT}/submit", data=data) as response:
            return await response.json()


async def submit_and_subscribe(filename, websocket, job_map):
    response = await submit_job(filename)
    await websocket.send(json.dumps({"action":"subscribe", "job_id":response['job_id']}))
    job_map[response['job_id']] = filename

async def collect_result(job_id, local_filename):
    """Collect the results for the given job and store"""

    newpath = infer_result_name(local_filename)

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{ENDPOINT}/{job_id}/result") as response:
            content = await response.text()

            with open(newpath,'w') as f:
                f.write(content)


def infer_result_name(input_name):
    """Calculate output name for annotated paper"""

    nameroot, _ = os.path.splitext(input_name)
    newpath = nameroot + "_annotated.xml"
    return newpath


async def handle_results(websocket, job_map, total_files):

    done = 0

    with tqdm.tqdm(desc="annotation progress", total=total_files) as pbar:
        while done < total_files:
            resptext = await websocket.recv()

            try:
                resp = json.loads(resptext)

                tqdm.tqdm.write(f"{job_map[resp['job_id']]} update: {resp['step']}={resp['status']}")

                if resp['step'] == 'annotate' and resp['status'] == 'complete':
                    await collect_result(resp['job_id'],job_map[resp['job_id']])
                    pbar.update()
                    done += 1

            except Exception as e:
                tqdm.tqdm.write(f"Could not handle response {resptext}: {e}")


async def execute(files: List[str]):
    """This is the real main meat of the app that 'main' wrapps"""

    WS_ENDPOINT = ENDPOINT.replace("http","ws", 1)
    uri = f"{WS_ENDPOINT}/ws"

    async with websockets.connect(uri) as websocket:

        done = 0

        futures = []
        tasks = set()
        job_ids = {}
        job_map = {}

        to_process = set([file for file in files if not os.path.exists(infer_result_name(file))])
        
        for file in files:
            if file not in to_process:
                print(f"Skip existing {file}")

        result_handler = asyncio.create_task(handle_results(websocket, job_map, len(to_process)))

        for file in tqdm.tqdm(to_process, desc="upload progress"):
            await submit_and_subscribe(file, websocket, job_map)

        await result_handler



@click.command()
@click.argument("files", nargs=-1, type=click.Path(file_okay=True, exists=True))
def main(files):
    """Run annotation process"""
    logging.basicConfig(level=logging.INFO)
    asyncio.get_event_loop().run_until_complete(execute(files))


if __name__ == "__main__":
    main() # pylint: disable=no-value-for-parameter