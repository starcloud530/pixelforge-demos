async function loadAtlas(path) {
  const url = new URL(path, document.baseURI);
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Could not load ${url.pathname}`);
  const atlas = await response.json();
  const sheet = new Image();
  sheet.src = new URL(atlas.image, url);
  await sheet.decode();
  return { atlas, sheet };
}

async function mountPlayer(player) {
  const canvas = player.querySelector("canvas");
  const context = canvas.getContext("2d");
  const clipSelect = player.querySelector("[data-clip]");
  const outfitSelect = player.querySelector("[data-outfit]");
  const playButton = player.querySelector("[data-play]");
  const frameOutput = player.querySelector("[data-frame]");
  const stepButtons = player.querySelectorAll("[data-step]");
  const [base, variant] = await Promise.all([
    loadAtlas(player.dataset.atlas),
    player.dataset.variant ? loadAtlas(player.dataset.variant) : null,
  ]);

  let source;
  let tag;
  let frames = [];
  let position = 0;
  let timer = null;

  function draw() {
    const frame = frames[position];
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.drawImage(source.sheet, frame.x, frame.y, frame.width, frame.height, 0, 0, canvas.width, canvas.height);
    frameOutput.value = `${position + 1} / ${frames.length} · ${frame.delayMs} ms`;
  }

  function stop() {
    window.clearTimeout(timer);
    timer = null;
    playButton.textContent = "播放";
    frameOutput.setAttribute("aria-live", "polite");
  }

  function advance() {
    timer = window.setTimeout(() => {
      if (tag.loop === "once" && position === frames.length - 1) {
        stop();
        return;
      }

      position = (position + 1) % frames.length;
      draw();
      advance();
    }, frames[position].delayMs);
  }

  function selectClip() {
    stop();
    source = outfitSelect?.value === "variant" ? variant : base;
    tag = source.atlas.tags.find((entry) => entry.name === clipSelect.value);
    frames = source.atlas.frames.filter((frame) => frame.index >= tag.from && frame.index <= tag.to);
    position = 0;
    playButton.disabled = frames.length === 1;
    for (const button of stepButtons) button.disabled = frames.length === 1;
    canvas.width = source.atlas.frameWidth;
    canvas.height = source.atlas.frameHeight;
    context.imageSmoothingEnabled = false;
    draw();
  }

  selectClip();
  player.querySelector(".player-fallback").hidden = true;
  canvas.hidden = false;
  player.querySelector(".player-controls").hidden = false;

  clipSelect.addEventListener("change", selectClip);
  outfitSelect?.addEventListener("change", selectClip);
  playButton.addEventListener("click", () => {
    if (timer !== null) {
      stop();
      return;
    }
    if (tag.loop === "once" && position === frames.length - 1) {
      position = 0;
      draw();
    }
    playButton.textContent = "暂停";
    frameOutput.setAttribute("aria-live", "off");
    advance();
  });
  stepButtons.forEach((button) => {
    button.addEventListener("click", () => {
      stop();
      position = (position + Number(button.dataset.step) + frames.length) % frames.length;
      draw();
    });
  });
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) stop();
  });
}

for (const player of document.querySelectorAll("[data-player]")) {
  mountPlayer(player).catch(() => {
    player.querySelector(".player-error").hidden = false;
  });
}
