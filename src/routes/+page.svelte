<script lang="ts">
  import { onMount } from 'svelte';

  let textInput = '';
  let file: File | null = null;
  let bionicText = '';
  let loading = false;

  let pdfjsLib: any;
  let pdfDoc: any = null;
  let currentPage = 1;
  let totalPages = 0;

  onMount(async () => {
    try {
      // @ts-ignore
      pdfjsLib = await import('pdfjs-dist/build/pdf.js');
      pdfjsLib.GlobalWorkerOptions.workerSrc = '/pdf.worker.js';
    } catch (e) {
      console.error('Failed to load pdfjs-dist on client:', e);
      alert('PDF 라이브러리를 로드하는 데 실패했습니다.');
    }
  });

  function handleFileChange(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      file = input.files[0];
      textInput = ''; // Clear text input if file is selected
      bionicText = '';
      pdfDoc = null;
      currentPage = 1;
      totalPages = 0;
    }
  }

  async function sendToBackend(text: string) {
    try {
      const response = await fetch('http://localhost:8000/bionic-reading', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: text }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      bionicText = data.processed_text;
    } catch (error) {
      console.error('Error converting text:', error);
      alert('텍스트 변환 중 오류가 발생했습니다.');
    } finally {
      loading = false;
    }
  }

  async function renderPage(num: number) {
    if (!pdfDoc || num < 1 || num > totalPages) return;

    loading = true;
    currentPage = num;
    bionicText = '';
    await new Promise((resolve) => setTimeout(resolve, 100)); // UI 업데이트 시간 확보

    try {
      const page = await pdfDoc.getPage(num);
      const content = await page.getTextContent();
      const pageText = content.items.map((item: any) => item.str).join(' ');
      await sendToBackend(pageText);
    } catch (e) {
      console.error(`Error rendering page ${num}:`, e);
      alert(`${num} 페이지를 렌더링하는 중 오류가 발생했습니다.`);
    } finally {
      loading = false;
    }
  }

  async function handleConvert() {
    loading = true;
    bionicText = '';
    pdfDoc = null;

    if (file) {
      const ext = file.name.split('.').pop()?.toLowerCase();

      if (ext === 'txt') {
        const reader = new FileReader();
        reader.onload = async (e) => {
          const text = e.target?.result as string;
          await sendToBackend(text);
        };
        reader.readAsText(file);
      } else if (ext === 'pdf') {
        if (!pdfjsLib) {
          alert('PDF 기능을 아직 로드 중입니다. 잠시 후 다시 시도해주세요.');
          loading = false;
          return;
        }
        try {
          const arrayBuffer = await file.arrayBuffer();
          pdfDoc = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
          totalPages = pdfDoc.numPages;
          await renderPage(1);
        } catch (e) {
          console.error('PDF 변환 중 오류:', e);
          alert('PDF를 처리하는 중 오류가 발생했습니다.');
          pdfDoc = null;
        } finally {
          loading = false;
        }
      } else {
        alert('현재는 txt, pdf 파일만 지원합니다.');
        loading = false;
      }
    } else if (textInput.trim()) {
      await sendToBackend(textInput);
    } else {
      alert('텍스트를 입력하거나 파일을 선택해주세요.');
      loading = false;
    }
  }
</script>

<svelte:head>
  <title>Bionic Reading 변환기</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700;800&display=swap');

    :root {
      --primary-color: #007bff;
      --secondary-color: #6c757d;
      --background-color: #f8f9fa;
      --text-color: #212529;
      --card-bg: #ffffff;
      --border-color: #dee2e6;
      --font-family: 'Nanum Gothic', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }
    body {
      font-family: var(--font-family);
      background-color: var(--background-color);
      color: var(--text-color);
      line-height: 1.6;
      margin: 0;
      padding: 2rem;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
    }
    .container {
      max-width: 800px;
      width: 100%;
      padding: 2rem;
      background-color: var(--card-bg);
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    h1 {
      text-align: center;
      color: var(--primary-color);
      margin-bottom: 2rem;
    }
    .controls {
      display: flex;
      flex-direction: column; /* Changed to column for textarea */
      gap: 1rem;
      margin-bottom: 2rem;
      align-items: stretch; /* Stretch items to fill width */
    }
    input[type="file"] {
      flex-grow: 1;
      border: 1px solid var(--border-color);
      padding: 0.5rem;
      border-radius: 4px;
    }
    textarea {
      width: 100%;
      min-height: 150px;
      padding: 0.8rem;
      border: 1px solid var(--border-color);
      border-radius: 4px;
      font-family: var(--font-family);
      font-size: 1rem;
      resize: vertical;
    }
    button {
      padding: 0.8rem 1.2rem; /* Increased padding for better click area */
      border: none;
      background-color: var(--primary-color);
      color: white;
      border-radius: 4px;
      cursor: pointer;
      transition: background-color 0.2s;
      align-self: flex-end; /* Align button to the right */
    }
    button:disabled {
      background-color: var(--secondary-color);
      cursor: not-allowed;
    }
    button:hover:not(:disabled) {
      background-color: #0056b3;
    }
    .loading-spinner {
      text-align: center;
      padding: 2rem;
      font-size: 1.2rem;
    }
    .result-container {
      border: 1px solid var(--border-color);
      padding: 1.5rem;
      border-radius: 8px;
      background-color: #fff;
      min-height: 200px;
    }
    .bionic-text {
      line-height: 1.8;
      font-size: 1.1rem;
      white-space: pre-wrap;
      word-wrap: break-word;
    }
    .pagination {
      display: flex;
      justify-content: center;
      align-items: center;
      margin-top: 1.5rem;
      gap: 1rem;
    }
    .pagination button {
      background-color: var(--secondary-color);
    }
     .pagination button:hover:not(:disabled) {
      background-color: #5a6268;
    }
  </style>
</svelte:head>

<div class="container">
  <h1>Bionic Reading 변환기</h1>

  <div class="controls">
    <input type="file" accept=".txt,.pdf" on:change={handleFileChange} />
    <textarea bind:value={textInput} placeholder="여기에 텍스트를 입력하세요..."></textarea>
    <button on:click={handleConvert} disabled={loading || (!file && !textInput.trim())}>
      {#if loading && !pdfDoc}변환중...{:else}변환 시작!{/if}
    </button>
  </div>

  {#if loading && !bionicText}
    <div class="loading-spinner">
      <span>⏳ 변환 중입니다...</span>
    </div>
  {/if}

  {#if bionicText}
    <div class="result-container">
      <div class="bionic-text">
        {@html bionicText}
      </div>
    </div>
  {/if}

  {#if pdfDoc}
    <div class="pagination">
      <button on:click={() => renderPage(currentPage - 1)} disabled={currentPage <= 1 || loading}>
        이전
      </button>
      <span>{currentPage} / {totalPages}</span>
      <button on:click={() => renderPage(currentPage + 1)} disabled={currentPage >= totalPages || loading}>
        다음
      </button>
    </div>
  {/if}
</div>