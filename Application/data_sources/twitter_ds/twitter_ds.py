
import json
import os






async def _parse():
    return 






def read_tweet(config, path):
    tweets_file_path = os.path.join(path, "tweet.json")
    with open(tweets_file_path, 'rb') as f: 
        lines = f.read().decode().replace("\n", "") 

    data = lines[lines.find('[') : lines.rfind(']')+1]
    jsonObj = json.loads(data)
