
import asyncio
import time
import functools
import concurrent.futures

##your blocking synchronous function
def print_counter(counter): 
        time.sleep(1) 
        print (f"THis is the counter {counter}") 
        return 

async def sample(): 
                loop = asyncio.get_event_loop() 
                executor = concurrent.futures.ThreadPoolExecutor(max_workers=5) 

                asyncio.run_coroutine_threadsafe(self.consumer(self.queue), loop)

                """
                _, _ = await asyncio.wait( 
                fs=[loop.run_in_executor(executor,   
                    functools.partial(print_counter, counter)) for counter in range(0, 20)], 
                return_when=asyncio.ALL_COMPLETED) 
                """

def main(loop): 
    tasks=  asyncio.gather(*[sample() for i in range(10)]) 
    comments = loop.run_until_complete(tasks) 
    return  


if __name__ == "__main__":
        loop = asyncio.get_event_loop()
        main(loop)
        loop.close()