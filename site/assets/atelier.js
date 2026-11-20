const lightbox = document.querySelector(".lightbox");
const enlarged = lightbox.querySelector("img");
const zoom = lightbox.querySelector("[data-zoom]");
const surface = lightbox.querySelector(".zoom-surface");
const scroller = lightbox.querySelector(".light-scroll");
const message = lightbox.querySelector(".light-message");
const statusText = message.querySelector("[data-image-status]");
const original = message.querySelector("[data-original]");

function showImage() {
  enlarged.hidden = false;
  message.hidden = true;
  zoom.disabled = false;
}

enlarged.addEventListener("load", showImage);
enlarged.addEventListener("error", () => {
  statusText.textContent = "未能加载图片。";
  original.hidden = false;
});

function resetZoom() {
  surface.classList.remove("magnified");
  zoom.setAttribute("aria-pressed", "false");
  zoom.textContent = "放大 2×";
  scroller.scrollTo(0, 0);
}

zoom.addEventListener("click", () => {
  const magnified = surface.classList.toggle("magnified");
  zoom.setAttribute("aria-pressed", String(magnified));
  zoom.textContent = magnified ? "适合窗口" : "放大 2×";
  scroller.scrollTo((scroller.scrollWidth - scroller.clientWidth) / 2, (scroller.scrollHeight - scroller.clientHeight) / 2);
});
lightbox.querySelector("[data-close]").addEventListener("click", () => lightbox.close());
lightbox.addEventListener("close", resetZoom);

for (const viewer of document.querySelectorAll("[data-viewer]")) {
  const stage = viewer.querySelector("[data-enlarge]");
  const picture = stage.querySelector("img");
  const caption = viewer.querySelector("[data-metric-label]");
  const choices = viewer.querySelectorAll("[data-choice]");
  if (lightbox.showModal) stage.setAttribute("aria-haspopup", "dialog");

  for (const choice of choices) {
    choice.addEventListener("click", (event) => {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      for (const other of choices) other.removeAttribute("aria-current");
      choice.setAttribute("aria-current", "true");
      picture.src = choice.href;
      picture.alt = choice.dataset.description;
      stage.href = choice.href;
      viewer.classList.toggle("detail-view", choice !== choices[0]);
      caption.textContent = choice.dataset.metric;
    });
  }

  stage.addEventListener("click", (event) => {
    if (!lightbox.showModal || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    zoom.disabled = true;
    enlarged.hidden = true;
    original.href = stage.href;
    original.hidden = true;
    statusText.textContent = "正在载入图片…";
    message.hidden = false;
    enlarged.src = stage.href;
    enlarged.alt = picture.alt;
    if (enlarged.complete && enlarged.naturalWidth) showImage();
    const selected = viewer.querySelector('[data-choice][aria-current="true"]');
    lightbox.querySelector("[data-light-title]").textContent = viewer.getAttribute("aria-label") + " · " + selected.textContent;
    lightbox.showModal();
    lightbox.querySelector("[data-close]").focus();
  });
}
