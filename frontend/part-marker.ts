const marker = document.querySelector<HTMLElement>("[data-part-marker]");

if (marker) {
  const audio = marker.querySelector<HTMLAudioElement>("audio");
  const startInput = document.querySelector<HTMLInputElement>("[name='start']");
  const endInput = document.querySelector<HTMLInputElement>("[name='end']");

  const formatTime = (value: number): string => {
    const minutes = Math.floor(value / 60);
    const seconds = value - minutes * 60;
    return `${minutes}:${seconds.toFixed(3).padStart(6, "0")}`;
  };

  marker.querySelectorAll<HTMLButtonElement>("[data-mark]").forEach((button) => {
    button.addEventListener("click", () => {
      if (!audio) return;
      const target = button.dataset.mark === "start" ? startInput : endInput;
      if (target) target.value = formatTime(audio.currentTime);
    });
  });
}
