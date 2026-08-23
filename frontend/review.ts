const root = document.querySelector<HTMLElement>("[data-review-player]");

if (root) {
  const audio = root.querySelector<HTMLAudioElement>("audio");
  const playButton = root.querySelector<HTMLButtonElement>("[data-play]");
  const status = root.querySelector<HTMLElement>("[data-playback-status]");
  const answerInput = document.querySelector<HTMLInputElement>("[data-answer-input]");
  const replayInput = document.querySelector<HTMLInputElement>("[name='replay_count']");
  const start = Number.parseFloat(root.dataset.startSeconds ?? "0");
  const end = Number.parseFloat(root.dataset.endSeconds ?? "0");
  let playCount = 0;

  if (!audio || !playButton || !Number.isFinite(start) || !Number.isFinite(end)) {
    throw new Error("Review audio controls are incomplete.");
  }

  const finishExcerpt = (): void => {
    audio.pause();
    audio.currentTime = end;
    playButton.textContent = "Replay excerpt";
    if (status) status.textContent = "Excerpt finished.";
    answerInput?.focus();
  };

  audio.addEventListener("timeupdate", () => {
    if (!audio.paused && audio.currentTime >= end) finishExcerpt();
  });
  audio.addEventListener("ended", finishExcerpt);
  audio.addEventListener("error", () => {
    if (status) status.textContent = "Audio could not be loaded. Refresh and try again.";
  });

  playButton.addEventListener("click", async () => {
    audio.pause();
    audio.currentTime = start;
    if (playCount > 0 && replayInput) {
      const current = Number.parseInt(replayInput.value || "0", 10);
      replayInput.value = String(Math.min(100, current + 1));
    }
    playCount += 1;
    try {
      await audio.play();
      playButton.textContent = "Restart excerpt";
      if (status) status.textContent = "Playing…";
    } catch {
      if (status) status.textContent = "Playback was blocked. Tap play again.";
    }
  });

  window.addEventListener("pagehide", () => audio.pause());
}
