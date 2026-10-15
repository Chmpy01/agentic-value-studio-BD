import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright
R=Path(__file__).parent
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  page=await b.new_page(viewport={'width':1280,'height':800})
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  await page.set_content((R/'index.html').read_text(),wait_until='domcontentloaded',timeout=30000)
  await page.locator('[data-step="5"]').click()
  await page.locator('[data-approve="rejected"]').click()
  await page.locator('#next').click()
  rejected=await page.locator('.run-detail h2').inner_text()
  assert rejected=='Approve'
  assert (await page.evaluate('window.__CVS_TEST__.state.approval'))=='rejected'
  print('PASS rejection blocks next stage')
  await page.locator('#reset').click()
  await page.locator('#traceToggle').click()
  assert await page.locator('.traceitem').count()>=1
  print('PASS expandable trace')
  await page.locator('[data-tab="contracts"]').click()
  await page.locator('[data-contract="permit"]').click()
  body=await page.locator('#sampleContract').inner_text()
  assert 'physicalControlAllowed' in body and 'false' in body
  print('PASS action permit explicitly non-actuating')
  bad=json.loads((R/'packs'/'office-runtime.json').read_text());bad['controls']['allowPhysicalControl']=True
  result=await page.evaluate('(p)=>window.__CVS_TEST__.validate(p)',bad)
  assert result
  print('PASS unsafe imported configuration rejected by UI contract')
  print('PAGE ERRORS',errors)
  await b.close()
asyncio.run(main())
