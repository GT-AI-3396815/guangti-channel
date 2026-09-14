const { chromium } = require('playwright-core');

(async () => {
  const results = [];
  const ok = (name, cond) => results.push(`${cond ? 'PASS' : 'FAIL'}  ${name}`);
  const browser = await chromium.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: true,
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });

  // 外部字体 CDN（Google Fonts / loli.net 镜像）可用性随网络环境波动，
  // 与被测应用本身无关：统一 mock 为空 CSS，字体走系统回退，保证测试确定性。
  await page.route(/fonts\.(googleapis|loli)\.net|gstatic\.com|gstatic\.loli\.net/, (route) =>
    route.fulfill({ status: 200, contentType: 'text/css', body: '' })
  );

  const consoleErrors = [];
  page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text()); });
  page.on('pageerror', (e) => consoleErrors.push('PAGEERROR: ' + e.message));

  // 1. load home
  await page.goto('http://127.0.0.1:8945/index.html', { waitUntil: 'load' });
  ok('home-section visible', await page.isVisible('#home-section'));
  ok('no JS errors on load', consoleErrors.length === 0);

  // 2. channel cards
  const cardCount = await page.locator('.channel-card').count();
  ok(`12 channel cards (got ${cardCount})`, cardCount === 12);
  const liveBadges = await page.locator('.channel-status.live').count();
  ok(`LIVE badges added (got ${liveBadges})`, liveBadges === 12);

  // 3. click ch02 card
  await page.locator('.channel-card[data-channel="ch02"]').first().click();
  await page.waitForTimeout(300);
  ok('ch02 page active after click', await page.isVisible('#page-ch02'));
  ok('home hidden in channel view', !(await page.isVisible('#home-section')));
  ok('hash set to #ch02', page.url().endsWith('#ch02'));
  ok('back button visible', await page.isVisible('#page-ch02 .channel-page-back'));

  // 4. back to home
  await page.locator('#page-ch02 .channel-page-back').click();
  await page.waitForTimeout(300);
  ok('home visible after back', await page.isVisible('#home-section'));
  ok('ch02 hidden after back', !(await page.isVisible('#page-ch02')));
  ok('hash back to #home', page.url().endsWith('#home'));

  // 4b. browser back button returns from channel to home
  await page.locator('.channel-card[data-channel="ch03"]').first().click();
  await page.waitForTimeout(300);
  await page.goBack();
  await page.waitForTimeout(300);
  ok('browser back returns to home', await page.isVisible('#home-section'));
  ok('hash after browser back is #home', page.url().endsWith('#home'));

  // 5. deep link #ch07
  await page.goto('http://127.0.0.1:8945/index.html#ch07', { waitUntil: 'load' });
  await page.waitForTimeout(300);
  ok('deep link #ch07 opens ch07', await page.isVisible('#page-ch07'));

  // 6. every channel opens and has real content
  for (let i = 1; i <= 12; i++) {
    const ch = 'ch' + String(i).padStart(2, '0');
    await page.evaluate((c) => showChannel(c), ch);
    await page.waitForTimeout(80);
    const visible = await page.isVisible('#page-' + ch);
    const textLen = await page.evaluate((c) => document.getElementById('page-' + c).innerText.length, ch);
    ok(`${ch} opens & has content (${textLen} chars)`, visible && textLen > 200);
  }
  await page.evaluate(() => showHome());

  // 7. no broken internal links (all in-page hrefs resolve; relative asset links like rss.xml are valid)
  const badHrefs = await page.evaluate(() => {
    const bad = [];
    document.querySelectorAll('a[href]').forEach((a) => {
      const h = a.getAttribute('href');
      if (!h) return;
      if (h.startsWith('#') || /^https?:/.test(h)) return;
      if (/^(\.\/)?[\w.\-]+\.(xml|html|pdf|jpg|png|txt)$/i.test(h)) return; // 合法相对资源
      bad.push(h);
    });
    return bad;
  });
  ok(`no broken internal hrefs (got ${JSON.stringify(badHrefs)})`, badHrefs.length === 0);

  // 7b. SEO / 社交分享 meta
  ok('meta description present', await page.locator('meta[name="description"]').count() === 1);
  ok('og:title present', await page.locator('meta[property="og:title"]').count() >= 1);
  ok('canonical present', await page.locator('link[rel="canonical"]').count() === 1);
  ok('JSON-LD present', await page.locator('script[type="application/ld+json"]').count() === 1);

  // 7c. 内容专业度：研判块 + 内容性质标注
  const jCount = await page.locator('.channel-page .judgment').count();
  ok(`judgment blocks >= 45 (got ${jCount})`, jCount >= 45);
  const noticeCount = await page.locator('.channel-page .hero-notice').count();
  ok(`hero-notice >= 8 (got ${noticeCount})`, noticeCount >= 8);

  // 7d. 站内搜索
  await page.fill('#site-search', '金砖');
  await page.waitForTimeout(250);
  const srCount = await page.locator('.search-result-item').count();
  ok(`search returns results (got ${srCount})`, srCount > 0);
  await page.locator('.search-result-item').first().click();
  await page.waitForTimeout(450);
  const activeCh = await page.evaluate(() => {
    const p = document.querySelector('.channel-page.active');
    return p ? p.id : null;
  });
  ok(`search result jumps to channel (got ${activeCh})`, !!activeCh);
  await page.evaluate(() => showHome());
  await page.waitForTimeout(200);

  // 7e. 更新日志 + RSS
  const logCount = await page.locator('#log-list li').count();
  ok(`update log entries >= 1 (got ${logCount})`, logCount >= 1);
  ok('RSS link present', await page.locator('a[href*="rss.xml"]').count() >= 1);

  // 7f. 频道切换条（在任意频道页可直达其他频道）
  await page.evaluate(() => showChannel('ch03'));
  await page.waitForTimeout(300);
  const chipsPerPage = await page.locator('#page-ch03 .ch-chip').count();
  ok(`channel switcher has 12 chips (got ${chipsPerPage})`, chipsPerPage === 12);
  const activeChip = await page.evaluate(() => {
    const c = document.querySelector('#page-ch03 .ch-chip.active');
    return c ? c.getAttribute('data-target') : null;
  });
  ok(`active chip marks current channel (got ${activeChip})`, activeChip === 'ch03');
  await page.locator('#page-ch03 .ch-chip[data-target="ch05"]').click();
  await page.waitForTimeout(400);
  ok('chip click switches channel', await page.isVisible('#page-ch05'));
  const activeChip5 = await page.evaluate(() => {
    const c = document.querySelector('#page-ch05 .ch-chip.active');
    return c ? c.getAttribute('data-target') : null;
  });
  ok(`active chip follows channel switch (got ${activeChip5})`, activeChip5 === 'ch05');

  // 7g. 上一频道 / 下一频道（首尾循环）
  const pagerNext = await page.locator('#page-ch05 .channel-pager .pager-btn.next').getAttribute('href');
  ok(`next pager points to #ch06 (got ${pagerNext})`, pagerNext === '#ch06');
  await page.locator('#page-ch05 .channel-pager .pager-btn.next').click();
  await page.waitForTimeout(400);
  ok('pager next switches to ch06', await page.isVisible('#page-ch06'));
  const wrapPrev = await page.locator('#page-ch01 .channel-pager .pager-btn.prev').getAttribute('href');
  ok(`first channel prev wraps to #ch12 (got ${wrapPrev})`, wrapPrev === '#ch12');

  // 7h. 阅读信息条（条数 + 预计时长）
  const infoText = await page.locator('#page-ch06 .channel-page-info').innerText();
  const infoFlat = infoText.replace(/\s+/g, ' ');
  ok(`reading info strip shows count & minutes (got "${infoFlat.slice(0, 46)}")`,
     /\d+\s*条内容/.test(infoText) && /约\s*\d+\s*分钟/.test(infoText));

  // 7h2. 日期一致性：导航日期 / 阅读信息条 / hero 日期必须一致（防止站点谎报"今日已更新"）
  const dateCheck = await page.evaluate(() => {
    const norm = (s) => (((s || '').match(/(\d{4})\D+(\d{1,2})\D+(\d{1,2})/) || []).slice(1)
      .map((x) => String(x).padStart(2, '0')).join('.'));
    const nav = (document.querySelector('.nav-date') || {}).textContent;
    const page = document.getElementById('page-ch06');
    const info = (page.querySelector('.channel-page-info') || {}).textContent;
    const hero = (page.querySelector('.hero-date') || {}).textContent;
    return { nav: norm(nav), info: norm(info), hero: norm(hero) };
  });
  ok(`dates consistent across nav/info/hero (${dateCheck.nav} / ${dateCheck.info} / ${dateCheck.hero})`,
     !!dateCheck.nav && dateCheck.nav === dateCheck.info && dateCheck.info === dateCheck.hero);

  // 7i. 阅读进度条 + 回到顶部
  await page.evaluate(() => showChannel('ch03'));
  await page.waitForTimeout(350);
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(400);
  const topHiddenAtTop = await page.evaluate(() => !document.querySelector('.fab-top').classList.contains('show'));
  ok('back-to-top hidden before scrolling', topHiddenAtTop);
  await page.evaluate(() => window.scrollTo(0, 3000));
  await page.waitForTimeout(450);
  const progressPct = await page.evaluate(() => parseFloat(document.querySelector('.read-progress').style.width) || 0);
  const topShown = await page.evaluate(() => document.querySelector('.fab-top').classList.contains('show'));
  ok(`progress bar advances on scroll (got ${progressPct}%)`, progressPct > 0);
  ok('back-to-top appears after scrolling', topShown);
  await page.locator('.fab-top').click();
  await page.waitForTimeout(1000);
  const backTopY = await page.evaluate(() => window.scrollY);
  ok(`back-to-top returns to top (scrollY=${backTopY})`, backTopY < 80);

  // 7j. 复制本页链接（本地链接同样可分享）
  await page.locator('.fab-copy').click();
  await page.waitForTimeout(450);
  ok('copy-link shows toast', await page.isVisible('#site-toast'));

  // 7k. 搜索：命中全部匹配卡片 + 准确计数 + 高亮 + 键盘
  await page.evaluate(() => showHome());
  await page.waitForTimeout(300);
  await page.fill('#site-search', '政策');
  await page.waitForTimeout(500);
  const srMulti = await page.locator('.search-result-item').count();
  ok(`search finds multiple matching cards (got ${srMulti}, expect >= 10)`, srMulti >= 10);
  const srChannels = await page.evaluate(() =>
    new Set([...document.querySelectorAll('.search-result-item')].map((i) => i.getAttribute('data-ch'))).size);
  ok(`search spans multiple channels (got ${srChannels})`, srChannels >= 2);
  const srLabel = await page.locator('.search-results .sr-count').innerText();
  const declared = parseInt((srLabel.match(/共\s*(\d+)/) || [])[1] || '0', 10);
  ok(`result count label matches actual hits (label=${declared}, shown=${srMulti})`, declared >= srMulti);
  ok('search highlights matched keyword', await page.locator('.search-results mark').count() >= 1);
  await page.keyboard.press('ArrowDown');
  await page.waitForTimeout(180);
  ok('arrow key selects a result', await page.locator('.search-result-item.active').count() === 1);
  await page.keyboard.press('Enter');
  await page.waitForTimeout(700);
  const jumpedCh = await page.evaluate(() => {
    const p = document.querySelector('.channel-page.active');
    return p ? p.id : null;
  });
  ok(`Enter opens the selected result (got ${jumpedCh})`, !!jumpedCh);
  await page.evaluate(() => showHome());
  await page.waitForTimeout(300);
  await page.fill('#site-search', '政策');
  await page.waitForTimeout(400);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(250);
  ok('Escape closes search dropdown', await page.evaluate(() =>
     getComputedStyle(document.getElementById('search-results')).display === 'none'));

  // 7l. “/” 快捷键聚焦搜索框
  await page.evaluate(() => { if (document.activeElement) document.activeElement.blur(); });
  await page.keyboard.press('/');
  await page.waitForTimeout(300);
  ok('/ shortcut focuses search box', await page.evaluate(() =>
     document.activeElement && document.activeElement.id === 'site-search'));

  // 7m. 外链安全 / RSS 自动发现 / 打印样式
  const unsafeLinks = await page.evaluate(() =>
    [...document.querySelectorAll('a[target="_blank"]')]
      .filter((a) => !(a.rel || '').includes('noopener') || !(a.rel || '').includes('noreferrer')).length);
  ok(`all target=_blank links hardened (unsafe=${unsafeLinks})`, unsafeLinks === 0);
  ok('RSS alternate link present', await page.locator('link[rel="alternate"][type="application/rss+xml"]').count() === 1);
  const hasPrintCss = await page.evaluate(() => [...document.styleSheets].some((s) => {
    try { return [...s.cssRules].some((r) => r.conditionText && r.conditionText.includes('print')); }
    catch (e) { return false; }
  }));
  ok('print stylesheet present', hasPrintCss);

  // 8. console errors overall
  ok(`no console errors overall (got ${consoleErrors.length}: ${consoleErrors.slice(0, 3).join(' | ')})`, consoleErrors.length === 0);

  // 9. screenshots: desktop home + mobile channel + desktop ch07 (renamed classes)
  await page.screenshot({ path: 'test/desktop-home.png', fullPage: false });
  await page.evaluate(() => showChannel('ch07'));
  await page.waitForTimeout(400);
  await page.screenshot({ path: 'test/desktop-ch07.png' });
  await page.evaluate(() => showChannel('ch03'));
  await page.waitForTimeout(400);
  await page.screenshot({ path: 'test/desktop-ch03.png' });
  const mob = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await mob.goto('http://127.0.0.1:8945/index.html', { waitUntil: 'load' });
  await mob.screenshot({ path: 'test/mobile-home.png' });
  await mob.locator('.channel-card[data-channel="ch01"]').first().click();
  await mob.waitForTimeout(400);
  await mob.screenshot({ path: 'test/mobile-ch01.png' });

  console.log(results.join('\n'));
  const fails = results.filter((r) => r.startsWith('FAIL')).length;
  console.log(`\n${results.length - fails}/${results.length} passed`);
  await browser.close();
  process.exit(fails ? 1 : 0);
})().catch((e) => { console.error('RUNNER ERROR:', e.message); process.exit(2); });
