#중요기사 찾기
print("flask 서버를 시작합니다")
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import os
import ollama
from ollama import chat
from ollama import ChatResponse
from transformers import pipeline, logging
from deep_translator import GoogleTranslator
from ollama import chat
from ollama import ChatResponse
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from ollama import chat, Client

app = Flask(__name__)
CORS(app)


#항상 뭔지 모르는 이유로 exaone이 태그를 달고 뒤에 이유를 붙여주는데 그거 방지용임.
def remove_reason_from_text(text: str) -> str:
    """
    긴 문장에서 '긍정적', '부정적', '중립적' 중 하나의 감정 태그를 추출합니다.
    """
    text = text.strip().replace(" ", "")  # 공백 제거

    if "긍정" in text:
        return "긍정적"
    elif "부정" in text:
        return "부정적"
    elif "중립" in text:
        return "중립적"
    else:
        return "Unknown"  # 혹은 None

    


# 경고 메시지 숨기기
logging.set_verbosity_error()



#같은 내용을 한번 더 처리해서 시간 낭비하는걸 방지하려고 만들었음
file_list = ["title.txt", "summary.txt", "tag.txt", "opinion.txt", "newopinion.txt", "img.txt"]

# 각 파일 존재 여부 확인하고 없으면 생성
for file_name in file_list:
    if not os.path.exists(file_name):
        with open(file_name, 'w', encoding='utf-8') as f:
            pass  # 빈 파일 생성
        print(f"{file_name} 파일을 생성했습니다.\n")
    else:
        print(f"{file_name} 파일이 이미 존재합니다.\n")


ollama_base = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
client = ollama.Client(host=ollama_base)

print("세팅이 완료되었습니다")


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/news_get', methods=['GET'])
def get_name():
    name = request.args.get('name')
    #요약된 기사들 담을 리스트 미리 초기화
    summarized_articles = []


    # 네이버 뉴스 URL
    url = "https://news.naver.com/"

    # 브라우저 설정
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # 최신 헤드리스 모드 사용
    chrome_options.add_argument("--disable-gpu")  # GPU 비활성화
    chrome_options.add_argument("--no-sandbox")  # 샌드박스 비활성화
    chrome_options.add_argument("--disable-dev-shm-usage")  # /dev/shm 사용 방지 (도커 환경에서 필수)
    chrome_options.add_argument("--window-size=1920x1080")  # 뷰포트 설정 (필요 시)

    # 드라이버 실행
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    driver.get(url)

    time.sleep(0.5)


    # 뉴스 링크를 저장할 리스트
    news_links = []




    # 뉴스 링크 추출
    try:
        # a 태그를 찾고, 필요한 클래스명을 사용하여 뉴스 링크를 가져옴
        a_tags = driver.find_elements(By.CSS_SELECTOR, 'a.cnf_news_area._cds_link')
        
        for a_tag in a_tags[:20]:  # 최대 20개만 추출
            link = a_tag.get_attribute("href")
            if link and link.startswith("https://n.news.naver.com/article"):
                news_links.append(link)

        #print("추출된 뉴스 링크:")
    except Exception as e:
        print(f"링크 추출 오류: {e}")




    # 각 링크에 들어가서 기사 내용과 제목 추출
    article_contents = []

    for link in news_links:
        try:
            driver.get(link)
            time.sleep(0.5)  # 페이지 로딩을 위해 잠시 대기

            # 기사 제목 추출
            title = None
            try:
                title_element = driver.find_element(By.CLASS_NAME, "media_end_head_title")
                title = title_element.text.strip()  # 제목 추출
            except Exception as e:
                print(f"기사 제목 추출 오류: {e}")

            
            # 기사 내용 추출
            article_content = None
            try:
                # article 태그를 찾아서 그 하위 태그들에서 텍스트를 추출
                article_element = driver.find_element(By.ID, "dic_area")
                article_content = article_element.text.strip()  # 텍스트 추출
            except Exception as e:
                print(f"기사 내용 추출 오류: {e}")



            # 이미지 URL 추출
            # 기본 이미지 URL 설정
            # 기본 이미지로 초기화
            # 기본 이미지 URL
            imgurl = "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEjJmIY5-iIha8iSLZHScoPWTW4v9gRX6hbAv3er304DcP3m-xngQeoWQ-UxrHdKGAQeXWRB_yqJFU9qqhyWmvf5hta2j6_h2Fd-5v0Qoyenkd_ZWDy7s5xQIh8z9Q_tt94kc96tFEeFRcg/s1600/noimg.gif"

            try:
                # elements (복수형)로 찾으면 없을 때도 오류 안 남
                img_elements = driver.find_elements(By.ID, "img1")
                
                if img_elements:
                    src = img_elements[0].get_attribute("src")
                    if src and src.strip():
                        imgurl = src.strip()

            except Exception as e:
                print(f"이미지 URL 추출 오류: {e}")




            
            
            if article_content:
                article_contents.append({
                    'url': link,
                    'title': title,
                    'content': article_content,
                    'img' : imgurl
                })
                # 미리보기 출력 (100자)
                #print(f"기사 크롤링 완료: {link}")
                
        except Exception as e:
            print(f"링크에서 기사 내용 추출 실패: {e}")

    # 브라우저 종료
    driver.quit()





    # 메시지를 통해 번호 선택하기
    response = chat(model='exaone3.5:2.4b', messages=[{
        'role': 'user',
        'content': f"""
    1. {article_contents[0]['title']}
    2. {article_contents[1]['title']}
    3. {article_contents[2]['title']}
    4. {article_contents[3]['title']}
    5. {article_contents[4]['title']}
    6. {article_contents[5]['title']}
    7. {article_contents[6]['title']}
    8. {article_contents[7]['title']}
    9. {article_contents[8]['title']}
    10. {article_contents[9]['title']}
    11. {article_contents[10]['title']}
    12. {article_contents[11]['title']}
    13. {article_contents[12]['title']}
    14. {article_contents[13]['title']}
    15. {article_contents[14]['title']}
    16. {article_contents[15]['title']}
    17. {article_contents[16]['title']}
    18. {article_contents[17]['title']}
    19. {article_contents[18]['title']}
    20. {article_contents[19]['title']}

    중에서 가장 중요한 뉴스를 골라서 아무말 없이 그냥 "번호만"말해줘 (아무 부호 없이 그냥 숫자 하나만)
    """,
    }])


    ###가장 중요한 뉴스 선정 완료
    raw_content = response['message']['content']
    num_str = re.sub(r'\D', '', raw_content)  # 숫자만 남김
    num = int(num_str)
    print("가장 중요한 뉴스 기사 목록:")
    print(f"\n제목: {article_contents[num - 1]['title']}")
    maintitle = article_contents[num - 1]['title']

    #뉴스 요약, 반대(다른) 여론 생성
    article_content = article_contents[num - 1]['content']




    isthere = -1
    #이미 있는지 확인
    with open("title.txt", "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if line.strip() == article_contents[num - 1]['title']:
                isthere = i # 0부터 시작
                break

    if isthere != -1:
        print("찾고있는 처리된 기사가 이미 저장되어있어서 저장된걸로 대체함.")
        target_line = isthere

        with open("summary.txt", "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i == target_line:
                    mainsummary = line.strip()
                    break

        with open("tag.txt", "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i == target_line:
                    maintage = line.strip()
                    break


        with open("opinion.txt", "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i == target_line:
                    mainopinion = line.strip()
                    break

        with open("newopinion.txt", "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i == target_line:
                    mainnewopinion = line.strip()
                    break

        with open("img.txt", "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i == target_line:
                    mainimg = line.strip()
                    break

    else:
        
        #동시저장 방지
        with open("title.txt", "a", encoding="utf-8") as f:
            f.write("동시저장 방지용 임시텍스트\n")  # 줄 추가

        with open("summary.txt", "a", encoding="utf-8") as f:
            f.write("동시저장 방지용 임시텍스트\n")  # 줄 추가

        with open("tag.txt", "a", encoding="utf-8") as f:
            f.write("동시저장 방지용 임시텍스트\n")  # 줄 추가

        with open("opinion.txt", "a", encoding="utf-8") as f:
            f.write("동시저장 방지용 임시텍스트\n")  # 줄 추가

        with open("newopinion.txt", "a", encoding="utf-8") as f:
            f.write("동시저장 방지용 임시텍스트\n")  # 줄 추가

        with open("img.txt", "a", encoding="utf-8") as f:
            f.write("동시저장 방지용 임시텍스트\n")  # 줄 추가


        with open("title.txt", "r", encoding="utf-8") as f:
            title_len = sum(1 for _ in f)

        last_index = title_len - 1  # 마지막 줄의 인덱스
        
        try:
            
            #제목 먼저 저장            
            with open("title.txt", "r", encoding="utf-8") as f_old, open("temp.txt", "w", encoding="utf-8") as f_new:
                for i, line in enumerate(f_old):
                    if i == last_index:
                        f_new.write(article_contents[num - 1]['title'] + "\n")   # 해당 줄은 새 내용으로
                    else:
                        f_new.write(line)       # 나머지는 그대로 복사

            os.replace("temp.txt", "title.txt")  # 임시 파일로 원본 덮어쓰기


            # 1. 한국어 요약 모델 설정
            summarizer = pipeline(
                "summarization",
                model="lcw99/t5-base-korean-text-summary"
            )
            # 4. 요약 실행
            summary = summarizer(
                article_content,
                max_length=150,
                min_length=50,
                do_sample=False
            )
            summary_text = summary[0]['summary_text']
            print(f"요약: {summary_text}\n")
            mainsummary = summary_text


            
            with open("summary.txt", "r", encoding="utf-8") as f_old, open("temp.txt", "w", encoding="utf-8") as f_new:
                for i, line in enumerate(f_old):
                    if i == last_index:
                        f_new.write(mainsummary + "\n")   # 해당 줄은 새 내용으로
                    else:
                        f_new.write(line)       # 나머지는 그대로 복사

            os.replace("temp.txt", "summary.txt")  # 임시 파일로 원본 덮어쓰기

            

            response: ChatResponse = chat(model='exaone3.5:2.4b', messages=[{
                'role': 'user',
                'content': f"'''{article_content}''' 이 뉴스기사를 대중의 관점으로 보았을 때 '긍정적', '부정적', '중립적' 중에 어떤것인지 '한 단어로(긍정적, 부정적, 중립적 중에 1가지만 이유 없이)' 대답해 주세요.(이유는 필요없음)",
            }])
            print(f"태그: {response.message.content}")
            maintage = remove_reason_from_text(response.message.content)


            with open("tag.txt", "r", encoding="utf-8") as f_old, open("temp.txt", "w", encoding="utf-8") as f_new:
                for i, line in enumerate(f_old):
                    if i == last_index:
                        f_new.write(maintage + "\n")   # 해당 줄은 새 내용으로
                    else:
                        f_new.write(line)       # 나머지는 그대로 복사

            os.replace("temp.txt", "tag.txt")  # 임시 파일로 원본 덮어쓰기



            
            response: ChatResponse = chat(model='exaone3.5:2.4b', messages=[{
                'role': 'user',
                'content': f"'''{article_content}''' 이 뉴스기사와 다른 의견이나 의문점을 한국어 한 문장으로 짧게 대답해 주세요.",
            }])
            print(f"의문점1: {response.message.content}")
            mainopinion = response.message.content


            with open("opinion.txt", "r", encoding="utf-8") as f_old, open("temp.txt", "w", encoding="utf-8") as f_new:
                for i, line in enumerate(f_old):
                    if i == last_index:
                        f_new.write(mainopinion + "\n")   # 해당 줄은 새 내용으로
                    else:
                        f_new.write(line)       # 나머지는 그대로 복사

            os.replace("temp.txt", "opinion.txt")  # 임시 파일로 원본 덮어쓰기




            response: ChatResponse = chat(model='exaone3.5:2.4b', messages=[{
                'role': 'user',
                'content': f"'''{article_content}''' 이 뉴스기사와 또 다른 의견이나 의문점을 한국어 한 문장으로 짧게 대답해 주세요.",
            }])
            print(f"의문점2: {response.message.content}")
            mainnewopinion = response.message.content


            with open("newopinion.txt", "r", encoding="utf-8") as f_old, open("temp.txt", "w", encoding="utf-8") as f_new:
                for i, line in enumerate(f_old):
                    if i == last_index:
                        f_new.write(mainnewopinion + "\n")   # 해당 줄은 새 내용으로
                    else:
                        f_new.write(line)       # 나머지는 그대로 복사

            os.replace("temp.txt", "newopinion.txt")  # 임시 파일로 원본 덮어쓰기


            mainimg = article_contents[num - 1]['img']


            with open("img.txt", "r", encoding="utf-8") as f_old, open("temp.txt", "w", encoding="utf-8") as f_new:
                for i, line in enumerate(f_old):
                    if i == last_index:
                        f_new.write(mainimg + "\n")   # 해당 줄은 새 내용으로
                    else:
                        f_new.write(line)       # 나머지는 그대로 복사

            os.replace("temp.txt", "img.txt")  # 임시 파일로 원본 덮어쓰기


        except Exception as e:
            print(f"오류 발생: {e}")









    # 내 관심사 뉴스 찾기
    # 경고 메시지 숨기기
    logging.set_verbosity_error()


    # 검색할 이름 입력
    encoded_name = urllib.parse.quote(name)  # 이름 인코딩

    url = f"https://search.naver.com/search.naver?where=news&ie=utf8&sm=nws_hty&query={encoded_name}"

    # URL로 이동
    # 브라우저 설정
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # 최신 헤드리스 모드 사용
    chrome_options.add_argument("--disable-gpu")  # GPU 비활성화
    chrome_options.add_argument("--no-sandbox")  # 샌드박스 비활성화
    chrome_options.add_argument("--disable-dev-shm-usage")  # /dev/shm 사용 방지 (도커 환경에서 필수)
    chrome_options.add_argument("--window-size=1920x1080")  # 뷰포트 설정 (필요 시)

    # 드라이버 실행
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    driver.get(url)
    time.sleep(2)  # 페이지가 로드될 때까지 잠시 대기

    # 뉴스 제목과 내용 저장할 리스트
    articles = []

    # 공통 클래스만 포함된 요소를 CSS Selector로 찾기
    news_items = driver.find_elements(By.CSS_SELECTOR, ".sds-comps-vertical-layout.sds-comps-full-layout")[:12]

    for item in news_items:
        try:
            title_element = item.find_element(By.CSS_SELECTOR, ".sds-comps-text.sds-comps-text-ellipsis-1.sds-comps-text-type-headline1")
            content_element = item.find_element(By.CSS_SELECTOR, ".sds-comps-text.sds-comps-text-ellipsis-3.sds-comps-text-type-body1")
        except:
            continue  # 제목이나 내용이 없으면 skip

        title = title_element.text.strip()
        content = content_element.text.strip()

        default_imgurl = "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEjJmIY5-iIha8iSLZHScoPWTW4v9gRX6hbAv3er304DcP3m-xngQeoWQ-UxrHdKGAQeXWRB_yqJFU9qqhyWmvf5hta2j6_h2Fd-5v0Qoyenkd_ZWDy7s5xQIh8z9Q_tt94kc96tFEeFRcg/s1600/noimg.gif"
        imgurl = default_imgurl

        try:
            # 공통 이미지 클래스가 포함된 요소들만 찾기
            img_elements = item.find_elements(By.CSS_SELECTOR, ".sds-comps-base-layout.sds-comps-inline-layout.sds-comps-image")
            for img in img_elements:
                width = img.get_attribute("width")
                height = img.get_attribute("height")
                src = img.get_attribute("src")

                if width == "104" and height == "104" and src and not src.startswith("data:image"):
                    src = src.strip()
                    if "src=" in src:
                        parsed_url = urllib.parse.urlparse(src)
                        query_params = urllib.parse.parse_qs(parsed_url.query)
                        real_src = query_params.get("src")
                        if real_src and real_src[0].strip():
                            imgurl = urllib.parse.unquote(real_src[0].strip())
                        else:
                            imgurl = src
                    else:
                        imgurl = src
                    break
        except Exception as e:
            print(f"이미지 URL 추출 오류: {e}")

        if title and content:
            articles.append({
                "title": title,
                "content": content,
                "img": imgurl
            })



    # 브라우저 종료
    driver.quit()




    # 메시지를 통해 번호 선택하기
    response = chat(model='exaone3.5:2.4b', messages=[{
        'role': 'user',
        'content': f"""
    1. {articles[0]['title']}
    2. {articles[1]['title']}
    3. {articles[2]['title']}
    4. {articles[3]['title']}
    5. {articles[4]['title']}
    6. {articles[5]['title']}
    7. {articles[6]['title']}
    8. {articles[7]['title']}
    9. {articles[8]['title']}
    10. {articles[9]['title']}

    중에서 가장 중요한 뉴스를 3개 골라서 아무말 없이 그냥 "번호만"말해줘 (대답 예시: 1 2 3)
    """,
    }])



    print(f"\n선택한 3개의 뉴스 번호 원본: {response.message.content}\n")

    # 모든 정수 숫자만 추출 (불규칙한 구분자 대응)
    selected_indexes = [int(n) - 1 for n in re.findall(r'\d+', response.message.content)]

    # 개수 확인해서 인덱스 지정
    selected1 = selected_indexes[0] if len(selected_indexes) > 0 else None
    selected2 = selected_indexes[1] if len(selected_indexes) > 1 else None
    selected3 = selected_indexes[2] if len(selected_indexes) > 2 else None

    print(f"선택된 첫 번째 뉴스 인덱스: {selected1}")
    print(f"선택된 두 번째 뉴스 인덱스: {selected2}")
    print(f"선택된 세 번째 뉴스 인덱스: {selected3}")



    #1, 2, 3 요약, 의문점 찾기
    def summarize_and_get_opinion(article_content, title, index):

        isthere = -1
        #이미 있는지 확인
        with open("title.txt", "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if line.strip() == title:
                    isthere = i # 0부터 시작
                    break

        if isthere != -1:
            print("찾고있는 처리된 기사가 이미 저장되어있어서 저장된걸로 대체함.")
            target_line = isthere

            with open("title.txt", "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if i == target_line:
                        new_title = line.strip()
                        break

            with open("summary.txt", "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if i == target_line:
                        new_summary_text = line.strip()
                        break

            with open("tag.txt", "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if i == target_line:
                        new_tags_e = line.strip()
                        break


            with open("opinion.txt", "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if i == target_line:
                        new_opinionans = line.strip()
                        break

            with open("newopinion.txt", "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if i == target_line:
                        new_newopinionans = line.strip()
                        break

            with open("img.txt", "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if i == target_line:
                        new_img = line.strip()
                        break

            # 요약과 의문점 저장
            article_info = {
                'title': new_title,
                'summary': new_summary_text,
                'opinion1': new_opinionans,
                'tags' : new_tags_e,
                'opinion2': new_newopinionans,
                'img' : new_img
            }
            return article_info

        else:
            
            #동시저장 방지
            with open("title.txt", "a", encoding="utf-8") as f:
                f.write("동시저장 방지용 임시텍스트\n")  # 줄 추가

            with open("summary.txt", "a", encoding="utf-8") as f:
                f.write("동시저장 방지용 임시텍스트\n")  # 줄 추가

            with open("tag.txt", "a", encoding="utf-8") as f:
                f.write("동시저장 방지용 임시텍스트\n")  # 줄 추가

            with open("opinion.txt", "a", encoding="utf-8") as f:
                f.write("동시저장 방지용 임시텍스트\n")  # 줄 추가

            with open("newopinion.txt", "a", encoding="utf-8") as f:
                f.write("동시저장 방지용 임시텍스트\n")  # 줄 추가

            with open("img.txt", "a", encoding="utf-8") as f:
                f.write("동시저장 방지용 임시텍스트\n")  # 줄 추가

            with open("title.txt", "r", encoding="utf-8") as f:
                title_len = sum(1 for _ in f)

            last_index = title_len - 1  # 마지막 줄의 인덱스




            
            try:
                
                #제목 먼저 저장                
                new_title = str(title).strip()  # 혹시 모를 타입 에러 방지 + 줄 끝 공백 제거
                with open("title.txt", "r", encoding="utf-8") as f_old, open("temp.txt", "w", encoding="utf-8") as f_new:
                    for i, line in enumerate(f_old):
                        if i == last_index:
                            f_new.write(new_title + "\n")   # 해당 줄은 새 내용으로
                        else:
                            f_new.write(line)       # 나머지는 그대로 복사

                os.replace("temp.txt", "title.txt")  # 임시 파일로 원본 덮어쓰기



                
                # 1. 한국어 요약 모델 설정
                summarizer = pipeline(
                    "summarization",
                    model="lcw99/t5-base-korean-text-summary"
                )
                # 4. 요약 실행
                summary = summarizer(
                    article_content,
                    max_length=150,
                    min_length=50,
                    do_sample=False
                )
                summary_text = summary[0]['summary_text']
                new_summary_text = str(summary_text).strip()
                
                with open("summary.txt", "r", encoding="utf-8") as f_old, open("temp.txt", "w", encoding="utf-8") as f_new:
                    for i, line in enumerate(f_old):
                        if i == last_index:
                            f_new.write(new_summary_text + "\n")   # 해당 줄은 새 내용으로
                        else:
                            f_new.write(line)       # 나머지는 그대로 복사

                os.replace("temp.txt", "summary.txt")  # 임시 파일로 원본 덮어쓰기



                # 의견 받기
                response: ChatResponse = chat(model='exaone3.5:2.4b', messages=[{
                    'role': 'user',
                    'content': f"'''{article_content}''' 이 뉴스기사와 다른 의견이나 의문점을 한국어 한 문장으로 짧게 대답해 주세요.",
                }])
                print(f"\n선택한 뉴스의 의문점1: {response.message.content}\n")

                opinionans = response.message.content
                new_opinionans = str(opinionans).strip()

                with open("opinion.txt", "r", encoding="utf-8") as f_old, open("temp.txt", "w", encoding="utf-8") as f_new:
                    for i, line in enumerate(f_old):
                        if i == last_index:
                            f_new.write(new_opinionans + "\n")   # 해당 줄은 새 내용으로
                        else:
                            f_new.write(line)       # 나머지는 그대로 복사

                os.replace("temp.txt", "opinion.txt")  # 임시 파일로 원본 덮어쓰기



                # 의견 받기
                response: ChatResponse = chat(model='exaone3.5:2.4b', messages=[{
                    'role': 'user',
                    'content': f"'''{article_content}''' 이 뉴스기사와 또 다른 의견이나 의문점을 한국어 한 문장으로 짧게 대답해 주세요.",
                }])
                print(f"\n선택한 뉴스의 의문점2: {response.message.content}\n")

                opinionans = response.message.content
                new_newopinionans = str(opinionans).strip()

                with open("newopinion.txt", "r", encoding="utf-8") as f_old, open("temp.txt", "w", encoding="utf-8") as f_new:
                    for i, line in enumerate(f_old):
                        if i == last_index:
                            f_new.write(new_newopinionans + "\n")   # 해당 줄은 새 내용으로
                        else:
                            f_new.write(line)       # 나머지는 그대로 복사

                os.replace("temp.txt", "newopinion.txt")  # 임시 파일로 원본 덮어쓰기


                

                response: ChatResponse = chat(model='exaone3.5:2.4b', messages=[{
                    'role': 'user',
                    'content': f"'''{article_content}''' 이 뉴스기사를 대중의 관점으로 보았을 때 '긍정적', '부정적', '중립적' 중에 어떤것인지 '한 단어로(긍정적, 부정적, 중립적 중에 1가지만 이유 없이)' 대답해 주세요.(이유는 필요없음)",
                }])
                print(f"\n선택한 뉴스의 태그: {response.message.content}\n")

                tags_e = remove_reason_from_text(response.message.content)
                new_tags_e = str(tags_e).strip()

                with open("tag.txt", "r", encoding="utf-8") as f_old, open("temp.txt", "w", encoding="utf-8") as f_new:
                    lines = f_old.readlines()  # 파일 전체 줄을 리스트로 읽음
                    for i, line in enumerate(lines):
                        if i == last_index:
                            f_new.write(new_tags_e + "\n")   # 해당 줄은 새 내용으로
                        else:
                            f_new.write(line)       # 나머지는 그대로 복사

                os.replace("temp.txt", "tag.txt")  # 임시 파일로 원본 덮어쓰기


                newimg = articles[index]['img']


                with open("img.txt", "r", encoding="utf-8") as f_old, open("temp.txt", "w", encoding="utf-8") as f_new:
                    for i, line in enumerate(f_old):
                        if i == last_index:
                            f_new.write(newimg + "\n")   # 해당 줄은 새 내용으로
                        else:
                            f_new.write(line)       # 나머지는 그대로 복사

                os.replace("temp.txt", "img.txt")  # 임시 파일로 원본 덮어쓰기       


                # 요약과 의문점 저장
                article_info = {
                    'title': new_title,
                    'summary': new_summary_text,
                    'opinion1': new_opinionans,
                    'tags' : new_tags_e,
                    'opinion2': new_newopinionans,
                    'img' : newimg
                }
                return article_info

            except Exception as e:
                print(f"오류 발생 (기사 {index+1}): {e}")
                return None




    # selected 값들을 리스트로 묶고 루프로 처리
    selected_indices = [selected1, selected2, selected3]

    for idx in selected_indices:
        if idx is not None and 0 <= idx < len(articles):
            article = articles[idx]
            summarized = summarize_and_get_opinion(article['content'], article['title'], idx)
            if summarized:
                summarized_articles.append({
                    'title': summarized['title'],
                    'summary': summarized['summary'],
                    'opinion1': summarized['opinion1'],
                    'tags': summarized['tags'],
                    'opinion2' : summarized['opinion2'],
                    'img' : summarized['img']
                })



    # 결과 출력
    print(f"\n\n\n--------------------------\n\n\n내 관심사 : {name}. 뉴스 기사 목록:")
    for i in range(min(3, len(summarized_articles))):  # 최대 3개까지 출력
        print(f"\n제목: {summarized_articles[i]['title']}")
        print(f"요약: {summarized_articles[i]['summary']}")
        print(f"태그: {summarized_articles[i]['tags']}")
        print(f"의문점1: {summarized_articles[i]['opinion1']}")
        print(f"의문점2: {summarized_articles[i]['opinion2']}")

    #print(f"\n\ntest1: {summarized_articles[0]}")
    #print(f"\n\ntest2: {summarized_articles[1]}")
    #print(f"\n\ntest3: {summarized_articles[2]}")
    #이런식으로 저장


    # 16개의 정보 반환,
    # {name}1 -> 가장 중요한 뉴스
    # {name}2~4 -> 내 관심사 뉴스
    # 가장 중요한 뉴스와 내 관심사 뉴스 정보를 반환하는 부분
    
    return jsonify(
        {
            # 가장 중요한 뉴스
            "title1": maintitle,
            "summary1": mainsummary,
            "tags1": maintage,
            "opinion1": mainopinion,
            "newopinion1" : mainnewopinion,
            "img1" : mainimg,

            # 내 관심사 뉴스 (최대 3개까지 안전하게 처리)
            "title2": summarized_articles[0]['title'] if len(summarized_articles) > 0 else "뉴스 없음",
            "title3": summarized_articles[1]['title'] if len(summarized_articles) > 1 else "뉴스 없음",
            "title4": summarized_articles[2]['title'] if len(summarized_articles) > 2 else "뉴스 없음",

            "summary2": summarized_articles[0]['summary'] if len(summarized_articles) > 0 else "뉴스 없음",
            "summary3": summarized_articles[1]['summary'] if len(summarized_articles) > 1 else "뉴스 없음",
            "summary4": summarized_articles[2]['summary'] if len(summarized_articles) > 2 else "뉴스 없음",

            "tags2": summarized_articles[0]['tags'] if len(summarized_articles) > 0 else "뉴스 없음",
            "tags3": summarized_articles[1]['tags'] if len(summarized_articles) > 1 else "뉴스 없음",
            "tags4": summarized_articles[2]['tags'] if len(summarized_articles) > 2 else "뉴스 없음",

            "opinion2": summarized_articles[0]['opinion1'] if len(summarized_articles) > 0 else "뉴스 없음",
            "opinion3": summarized_articles[1]['opinion1'] if len(summarized_articles) > 1 else "뉴스 없음",
            "opinion4": summarized_articles[2]['opinion1'] if len(summarized_articles) > 2 else "뉴스 없음",

            "newopinion2": summarized_articles[0]['opinion2'] if len(summarized_articles) > 0 else "뉴스 없음",
            "newopinion3": summarized_articles[1]['opinion2'] if len(summarized_articles) > 1 else "뉴스 없음",
            "newopinion4": summarized_articles[2]['opinion2'] if len(summarized_articles) > 2 else "뉴스 없음",

            "img2": summarized_articles[0]['img'] if len(summarized_articles) > 0 else "뉴스 없음",
            "img3": summarized_articles[1]['img'] if len(summarized_articles) > 1 else "뉴스 없음",
            "img4": summarized_articles[2]['img'] if len(summarized_articles) > 2 else "뉴스 없음",
 
            
        }
    ), 200




if __name__ == '__main__':
  app.run('0.0.0.0',port=5000,debug=False)
