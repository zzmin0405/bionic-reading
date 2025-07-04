// place files you want to import through the `$lib` alias in this folder.

export function bionicReading(text: string): string {
  return text.replace(/[^\s]+/g, (word) => {
    // 숫자가 포함된 단어라면
    if (/\d/.test(word)) {
      // 숫자 부분만 굵게
      return word.replace(/(\d+)/g, '<b>$1</b>');
    } else {
      // 일반 단어는 앞부분만 굵게
      const split = Math.ceil(word.length / 2);
      return `<b>${word.slice(0, split)}</b>${word.slice(split)}`;
    }
  });
}
