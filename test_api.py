import sys, os, asyncio
from dotenv import load_dotenv
sys.path.append('admission-center/backend')
os.chdir('admission-center/backend')
load_dotenv('.env')
from routers.admission import get_trainees
async def test():
    try:
        res = await get_trainees(None, None, None, {})
        print('Success, found', len(res))
    except Exception as e:
        import traceback
        traceback.print_exc()
asyncio.run(test())
