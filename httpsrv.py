import asyncio
import os
from urllib.parse import unquote
import json
import config
from helpers.cameras import generate_hash

files = {}

async def handle_request(reader, writer):
    async def quit():
        response = b'HTTP/1.1 404 Not Found\n\nFile not found'
        writer.write(response)
        await writer.drain()
        writer.close() 

    try:
        request = await reader.read(1024)
        request = request.decode("utf-8")

        hash = unquote(request.split()[1][1:])

        # print(config.files)

        file_name = files.get(hash)
    except Exception as Ex:
        print(Ex)
        await quit()
        return

    if file_name is None:
        await quit()
        return     

    if file_name == '':
        await quit()
        return
    
    fn = '_'.join(file_name.lstrip(config.videos_path + '\\').split('\\')).replace(' ', '_')

    if os.path.isfile(file_name):
        with open(file_name, 'rb') as file:
            file_contents = file.read()
        response = f'HTTP/1.1 200 OK\nContent-Type: video/mp4\nContent-Disposition: attachment; filename="{os.path.basename(file_name)}"\nContent-Length: {len(file_contents)}\n\n'.encode("utf-8") + file_contents
        writer.write(response)
    else:
        await quit()
        return 

    await writer.drain()
    writer.close()

async def main():
    server = await asyncio.start_server(handle_request, config.base_url, config.base_port)

    print(f'Сервер запущен {config.base_url}:{config.base_port}')

    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())