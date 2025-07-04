from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import math
import re
import logging

# 형태소 분석기 (KoNLPy)
from konlpy.tag import Okt

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS 설정
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 요청 데이터 모델
class TextRequest(BaseModel):
    text: str

# 형태소 분석기 인스턴스
okt = Okt()

def apply_bionic_reading_simple(text: str):
    """
    간단한 바이오닉 리딩: 형태소 분석 없이 단어별로 앞부분을 굵게 처리
    """
    try:
        words = re.findall(r'\S+', text)
        spaces = re.findall(r'\s+', text)
        result_html = ""
        for i, word in enumerate(words):
            # 숫자나 특수문자만 있는 경우
            if re.match(r'^[^\w가-힣]+$', word):
                result_html += word
            else:
                actual_chars = re.findall(r'[\w가-힣]', word)
                if actual_chars:
                    char_count = len(actual_chars)
                    if char_count <= 2:
                        bold_length = 1
                    elif char_count <= 4:
                        bold_length = 2
                    elif char_count <= 6:
                        bold_length = 3
                    else:
                        bold_length = math.ceil(char_count * 0.4)
                    bold_part = ""
                    normal_part = ""
                    char_index = 0
                    for char in word:
                        if re.match(r'[\w가-힣]', char):
                            if char_index < bold_length:
                                bold_part += char
                            else:
                                normal_part += char
                            char_index += 1
                        else:
                            if char_index < bold_length:
                                bold_part += char
                            else:
                                normal_part += char
                    result_html += f"<b>{bold_part}</b>{normal_part}"
                else:
                    result_html += word
            if i < len(spaces):
                result_html += spaces[i]
        return result_html
    except Exception as e:
        logger.error(f"Error in apply_bionic_reading_simple: {str(e)}")
        raise e

def apply_bionic_reading_advanced(text: str):
    """
    고급 바이오닉 리딩: 형태소 분석 결과에 따라 품사별로 굵게 처리
    """
    try:
        morphs = okt.pos(text, norm=True, stem=True)
        result_html = ""
        pos_bold_ratio = {
            'Noun': 0.4, 'Verb': 0.4, 'Adjective': 0.4, 'Adverb': 0.3, 'Determiner': 0.3,
            'Exclamation': 0.3, 'Josa': 0.2, 'Eomi': 0.2, 'PreEomi': 0.2, 'Conjunction': 0.2,
            'Punctuation': 0.0, 'Foreign': 0.4, 'Alpha': 0.4, 'Number': 0.4, 'Unknown': 0.3,
            'KoreanParticle': 0.2,
        }
        for i, (word, pos) in enumerate(morphs):
            actual_chars = re.findall(r'[\w가-힣]', word)
            char_count = len(actual_chars)
            bold_length = 0
            if char_count > 0:
                ratio = pos_bold_ratio.get(pos, 0.3)
                bold_length = math.ceil(char_count * ratio)
                if bold_length == 0 and char_count > 0 and pos not in ['Punctuation']:
                    bold_length = 1
            bold_part = ""
            normal_part = ""
            current_bold_count = 0
            for char in word:
                if re.match(r'[\w가-힣]', char):
                    if current_bold_count < bold_length:
                        bold_part += char
                        current_bold_count += 1
                    else:
                        normal_part += char
                else:
                    if current_bold_count < bold_length and pos not in ['Punctuation']:
                        bold_part += char
                    else:
                        normal_part += char
            if bold_part or normal_part:
                result_html += f"<b>{bold_part}</b>{normal_part}"
            else:
                result_html += word
            if i < len(morphs) - 1:
                result_html += " "
        return result_html.strip()
    except Exception as e:
        logger.error(f"Error in apply_bionic_reading_advanced: {str(e)}")
        if "JVMNotFoundException" in str(e) or "No JVM shared library file" in str(e):
            raise HTTPException(status_code=500, detail="텍스트 처리 중 오류가 발생했습니다. Java Development Kit(JDK)가 설치되어 있고 JAVA_HOME 환경 변수가 올바르게 설정되었는지 확인해주세요: " + str(e))
        else:
            raise HTTPException(status_code=500, detail="텍스트 처리 중 오류가 발생했습니다: " + str(e))

@app.post("/process")
async def process_text(request: TextRequest):
    try:
        logger.info(f"Processing text: {request.text[:50]}...")
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="텍스트가 비어있습니다.")
        processed_text = apply_bionic_reading_simple(request.text)
        logger.info("Text processing completed successfully")
        return {"processed_text": processed_text}
    except Exception as e:
        logger.error(f"Error processing text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"텍스트 처리 중 오류가 발생했습니다: {str(e)}")

@app.post("/bionic-reading")
async def bionic_reading_endpoint(request: TextRequest):
    try:
        logger.info(f"Processing advanced bionic reading: {request.text[:50]}...")
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="텍스트가 비어있습니다.")
        processed_text = apply_bionic_reading_advanced(request.text)
        logger.info("Advanced bionic reading completed successfully")
        return {"processed_text": processed_text}
    except Exception as e:
        logger.error(f"Error in advanced bionic reading: {str(e)}")
        raise HTTPException(status_code=500, detail=f"고급 바이오닉 리딩 처리 중 오류가 발생했습니다: {str(e)}")

@app.get("/")
async def read_root():
    return {"message": "Hello, Bionic Reading Backend!", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "서버가 정상적으로 실행 중입니다."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
