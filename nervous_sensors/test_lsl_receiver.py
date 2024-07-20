from pylsl import StreamInlet, resolve_streams
import numpy as np
import asyncio
    
async def main():
    streams = resolve_streams(wait_time=1.0)
    for stream in streams:
        stream.inlet = StreamInlet(stream)
        print("Found inlet", stream.name(), "of type", stream.type(), "with nominal rate", stream.nominal_srate())
        stream.inlet.flush()
    
    while True:
        for stream in streams:
            if stream.type() == "ECG":
                stream.chunk, stream.timestamp = stream.inlet.pull_chunk(timeout=0.0, max_samples=10000)
                if stream.timestamp :
                    stream.chunk = np.array(stream.chunk).flatten()
                    # WARNING : rebuild timestamp properly as LSL is doing weired things with timestamps
                    for x in range(len(stream.timestamp)-1):
                        stream.timestamp[x+1] = stream.timestamp[x] + 1.0/stream.nominal_srate()
                    print(stream.name(), " inlet received : ", len(stream.chunk), " samples at time ", stream.timestamp[0])
            if stream.type() == "EDA":
                stream.chunk, stream.timestamp = stream.inlet.pull_chunk(timeout=0.0, max_samples=10000)
                if stream.timestamp:
                    stream.chunk = np.array(stream.chunk).flatten()
                    print(stream.name(), " inlet received : ", len(stream.chunk), " samples at time ", stream.timestamp[0])
        await asyncio.sleep(1.0)

if __name__ == '__main__':
    asyncio.run(main())