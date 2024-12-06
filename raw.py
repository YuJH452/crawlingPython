from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

# Chrome 드라이버 설정
chrome_options = webdriver.ChromeOptions()
download_path = os.path.join(os.getcwd(), "downloads")
if not os.path.exists(download_path):
    os.makedirs(download_path)

chrome_options.add_experimental_option('prefs', {
    "download.default_directory": download_path,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True,
    "profile.default_content_settings.popups": 0,
    "download.default_directory": download_path
})

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

try:
    # 개인정보 목록 페이지 URL
    list_url = 'https://www.law.go.kr/precSc.do?menuId=7&subMenuId=47&tabMenuId=213&query=%EA%B0%9C%EC%9D%B8%EC%A0%95%EB%B3%B4'
    driver.get(list_url)
    
    # 페이지가 로드될 때까지 대기
    print("기본 페이지 로딩 대기 중...")
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, 'left_list_bx')))
    time.sleep(2)

    total_downloaded = 0
    current_page = 1
    max_pages = 36  # 총 36페이지

    while current_page <= max_pages:
        try:
            print(f"\n=== 페이지 {current_page} 처리 시작 ===")
            
            # 현재 페이지의 항목들 가져오기
            items = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.left_list_bx li'))
            )
            
            # 실제 항목 수는 발견된 항목의 절반
            items = items[:len(items)//2]
            
            # 중복 제거: id 속성이 있는 항목만 선택
            items = [item for item in items if item.get_attribute('id')]
            
            print(f"현재 페이지의 항목 수: {len(items)}")
            
            # 각 항목 처리
            for idx, item in enumerate(items, 1):
                try:
                    print(f"항목 {idx}/{len(items)} 처리 중...")
                    
                    # 항목의 ID 가져오기
                    item_id = item.get_attribute('id')
                    print(f"항목 ID: {item_id}")
                    
                    # 현재 처리 중인 전체 번호 계산
                    total_item_number = (current_page - 1) * len(items) + idx
                    
                    # 항목 클릭
                    item.click()
                    time.sleep(2)
                    
                    # 저장 버튼 클릭
                    save_btn = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.ID, "bdySaveBtn"))
                    )
                    save_btn.click()
                    time.sleep(2)
                    
                    # PDF 저장 버튼 클릭
                    pdf_btn = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.ID, "FileSavePdf"))
                    )
                    pdf_btn.click()
                    time.sleep(2)
                    
                    # 최종 저장 버튼 클릭
                    final_save_btn = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.ID, "aBtnOutPutSave"))
                    )
                    final_save_btn.click()
                    
                    # PDF 다운로드 완료 대기
                    time.sleep(5)
                    
                    # 다운로드된 파일 이름 변경
                    downloaded_files = os.listdir(download_path)
                    if downloaded_files:
                        # 가장 최근에 다운로드된 파일 찾기
                        latest_file = max([os.path.join(download_path, f) for f in downloaded_files], key=os.path.getctime)
                        file_name, file_extension = os.path.splitext(os.path.basename(latest_file))
                        new_filename = f"{file_name}_{total_item_number:03d}{file_extension}"
                        new_filepath = os.path.join(download_path, new_filename)
                        
                        # 파일 이름 변경 시도
                        try:
                            if os.path.exists(latest_file):
                                os.rename(latest_file, new_filepath)
                                print(f"파일 이름 변경 완료: {new_filename}")
                        except Exception as rename_error:
                            print(f"파일 이름 변경 실패: {str(rename_error)}")
                    
                    total_downloaded += 1
                    print(f"항목 {idx}/{len(items)} PDF 다운로드 완료 (총 {total_downloaded}개)")
                    
                except Exception as e:
                    print(f"항목 {idx} 처리 중 오류: {str(e)}")
                    continue
            
            # PDF 다운로드 테스트 건너뛰기
            print(f"=== 페이지 {current_page} 확인 완료 ===")
            
            if current_page < max_pages:
                try:
                    # 다음 페이지로 이동
                    next_page = str(current_page + 1)
                    print(f"다음 페이지 {next_page}로 이동 시도...")
                    
                    # 현재 페이지가 5의 배수이면 다음 블록으로 이동
                    if current_page % 5 == 0:
                        print(f"페이지 블록 전환 필요 (현재: {current_page})")
                        next_block = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, "//div[@class='paging']//a[contains(@onclick, 'movePage') and .//img[@alt='다음으로']]"))
                        )
                        next_block.click()
                        time.sleep(2)
                        current_page += 1
                    else:
                        # 현재 블록 내에서 다음 페이지 클릭
                        next_page_xpath = f"//div[@class='paging']//ol//a[text()='{next_page}']"
                        next_page_element = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, next_page_xpath))
                        )
                        next_page_element.click()
                        time.sleep(2)
                        current_page += 1
                except Exception as e:
                    print(f"페이지 이동 중 오류 발생: {str(e)}")
                    break
            else:
                break

        except Exception as e:
            print(f"페이지 처리 중 오류 발생: {str(e)}")
            break
    print(f"총 다운로드한 파일 수: {total_downloaded}개")

except Exception as e:
    print(f"전체 실행 중 오류 발생: {e}")

finally:
    print("\n브라우저를 종료합니다...")
    driver.quit()
    print("프로그램이 안전하게 종료되었습니다.")