from typing import AsyncGenerator, Any, Callable

class Stream:
    BUFFER_SIZE = 1024
    DELIMITER = "://"

    async def stream(self, outputstream: Callable[[bytes], None], source: str) -> AsyncGenerator[Any, Any, Any]:
        raise NotImplementedError("stream method must be implemented in subclasses")

    async def receive(self, inputstream: Callable[[int], bytes], saveto: str) -> AsyncGenerator[Any, Any, Any]:
        raise NotImplementedError("receive method must be implemented in subclasses")

    async def write(self, outputstream: Callable[[bytes], None], data: bytes) -> None:
        # client_socket.broadcast
        outputstream(data)

    async def read(self, inputstream: Callable[[int], bytes], file_size: int) -> None:
        # client_socket.recv
        return inputstream(file_size)

class FileStream(Stream):
    METADATA = "FILE"

    async def stream(self, outputstream: Callable[[bytes], None], source: str) -> AsyncGenerator[Any, Any, Any]:
        try:
            with open(source, "rb") as f:
                while True:
                    chunk = f.read(self.BUFFER_SIZE)
                    if not chunk:
                        break
                    await self.write(outputstream, chunk)
        except FileNotFoundError:
            raise FileNotFoundError("File not found: {}".format(source))
        except Exception as e:
            raise e

    async def receive(self, inputstream: Callable[[int], bytes], file_size: int) -> AsyncGenerator[Any, Any, Any]:
        try:
            remaining_size = file_size
            while remaining_size > 0:
                chunk_size = min(remaining_size, self.BUFFER_SIZE)
                chunk = await self.read(inputstream, remaining_size)
                if not chunk:
                    break
                yield chunk
                remaining_size -= chunk_size
        except ConnectionError:
            raise ConnectionError("Connection error occurred")
        except Exception as e:
            raise e

class VideoStream(Stream):
    METADATA = "VIDEO"

    async def stream(self, outputstream: Callable[[bytes], None], source: str) -> None:
        try:
            # Your video streaming implementation here
            pass
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Video file not found: {source}") from e
        except Exception as e:
            raise e

    async def receive(self, inputstream: Callable[[int], bytes], file_size: int) -> None:
        try:
            # Your video receiving implementation here
            pass
        except ConnectionError as e:
            raise ConnectionError("Connection error occurred") from e
        except Exception as e:
            raise e


class AudioStream(Stream):
    METADATA = "AUDIO"

    async def stream(self, outputstream: Callable[[bytes], None], source: str) -> None:
        try:
            # Your audio streaming implementation here
            pass
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Audio file not found: {source}") from e
        except Exception as e:
            raise e

    async def receive(self, inputstream: Callable[[int], bytes], file_size: int) -> None:
        try:
            # Your audio receiving implementation here
            pass
        except ConnectionError as e:
            raise ConnectionError("Connection error occurred") from e
        except Exception as e:
            raise e

class StreamManager(Stream):
    async def stream(self, client_socket, source: str) -> AsyncGenerator[Any, Any, Any]:
        # Receive metadata indicating the type of content
        metadata = client_socket.recv(Stream.BUFFER_SIZE).decode()

        # # Determine the type of content based on metadata
        # if metadata.startswith("FILE"):
        #     receive_file(client_socket)
        # elif metadata.startswith("VIDEO"):
        #     receive_video(client_socket)
        # elif metadata.startswith("AUDIO"):
        #     receive_audio(client_socket)
        # else:
        #     print("Unknown content type")

    async def receive(self, socket, saveto: str) -> AsyncGenerator[Any, Any, Any]:
        return
