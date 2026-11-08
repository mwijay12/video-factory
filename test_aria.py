import asyncio
import edge_tts

async def test_aria():
    text = "God has not forgotten you. He sees every tear. Trust Him today."
    tts = edge_tts.Communicate(text=text, voice='en-US-AriaNeural', rate='-8%')
    await tts.save('output/test_aria.mp3')
    print('Aria voice test saved to output/test_aria.mp3')

asyncio.run(test_aria())
