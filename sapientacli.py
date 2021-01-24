import websockets
import click
import asyncio
import json
import os
import aiohttp
from tqdm import tqdm

ENDPOINT = os.environ.get("SAPIENTA_ENDPOINT", "https://sapienta.papro.org.uk")


async def submit_job(file_path: str) -> dict:
    """Submit job for processing, return ID on queue"""


    data = {'file': open(file_path, 'rb')}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{ENDPOINT}/submit", data=data) as response:
            return await response.json()


async def submit_and_subscribe(filename, websocket):
    response = await submit_job(filename)
    await websocket.send(json.dumps({"action":"subscribe", "job_id":response['job_id']}))
    return response['job_id']

async def collect_result(job_id, local_filename):
    """Collect the results for the given job and store"""

    nameroot, _ = os.path.splitext(local_filename)

    newpath = nameroot + "_annotated.xml"

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{ENDPOINT}/{job_id}/result") as response:
            content = await response.text()

            with open(newpath,'w') as f:
                f.write(content)     


async def execute(files):
    """This is the real main meat of the app that 'main' wrapps"""

    WS_ENDPOINT = ENDPOINT.replace("http","ws", 1)
    uri = f"{WS_ENDPOINT}/ws"

    async with websockets.connect(uri) as websocket:

        responses = 0

        futures = []

        for file in files:
            futures.append(submit_and_subscribe(file, websocket))
            responses += 1

        job_ids = await asyncio.gather(*futures)

        job_map = {job_id:filename for job_id, filename in zip(job_ids, files)}

        steps = sum([2 if file.endswith(".xml") else 3 for file in files])

        with tqdm(total=steps) as t:

            while responses > 0:
                resptext = await websocket.recv()

                try:
                    resp = json.loads(resptext)
                    t.update()

                    tqdm.write(f"{job_map[resp['job_id']]} update: {resp['step']}={resp['status']}")

                    if resp['step'] == 'annotate' and resp['status'] == 'complete':
                        await collect_result(resp['job_id'],job_map[resp['job_id']])
                        responses -= 1

                except Exception as e:
                    tqdm.write(f"Could not handle response {resptext}: {e}")



@click.command()
@click.argument("files", nargs=-1, type=click.Path(file_okay=True, exists=True))
def main(files):
    """Run annotation process"""
    asyncio.get_event_loop().run_until_complete(execute(files))


if __name__ == "__main__":
    main() # pylint: disable=no-value-for-parameter