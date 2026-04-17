// ===================================================
// 1. 시계 기능
// ===================================================
(function setupClock() {
    const clockElement = document.getElementById('clock');
    if (!clockElement) return;

    function updateClock() {
        const now = new Date();
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        clockElement.textContent = `${hours}:${minutes}`;
    }

    updateClock();
    setInterval(updateClock, 1000);
})();


// ===================================================
// 2. 이미지 캐러셀(슬라이드) 기능
// ===================================================
(function setupCarousel() {
    const track = document.querySelector('.track');
    const prevButton = document.querySelector('.prev');
    const nextButton = document.querySelector('.next');
    if (!track || !prevButton || !nextButton) return;
    
    const slides = Array.from(track.children);
    let currentIndex = 0;

    function updateSlidePosition() {
        if (slides.length === 0) return;
        const slideWidth = slides[0].getBoundingClientRect().width;
        const offset = -currentIndex * slideWidth;
        track.style.transform = `translateX(${offset}px)`;
        
        prevButton.disabled = currentIndex === 0;
        nextButton.disabled = currentIndex === slides.length - 1;
    }

    prevButton.addEventListener('click', () => {
        if (currentIndex > 0) {
            currentIndex--;
            updateSlidePosition();
        }
    });

    nextButton.addEventListener('click', () => {
        if (currentIndex < slides.length - 1) {
            currentIndex++;
            updateSlidePosition();
        }
    });

    window.addEventListener('resize', updateSlidePosition);
    updateSlidePosition();
})();


// ===================================================
// 3. 실시간 그래프 업데이트 기능 (5초 주기)
// ===================================================
(function setupRealtimeGraph() {
    const graphImage = document.getElementById('graph-image');
    if (!graphImage) return;

    function updateGraph() {
        const baseURL = graphImage.dataset.src;
        if (baseURL) {
            graphImage.src = `${baseURL}?t=${new Date().getTime()}`;
        }
    }

    updateGraph();
    setInterval(updateGraph, 10000);
})();


// ===================================================
// 4. 실시간 혼잡도 정보 업데이트 기능 (5초 주기)
// ===================================================
(function setupCongestionMonitor() {
    // 설정
    const config = {
        apiUrl: document.querySelector('.population-details')?.dataset.url || '/stream/status/supermaket.mp4/',
        updateInterval: 5000 // 5초로 통일
    };

    // UI 요소들
    const elements = {
        // 막대 그래프
        bar: document.getElementById('congestion-bar'),
        vBars: document.querySelectorAll('.v-bar'),
        
        // 텍스트 정보
        currentPeople: document.getElementById('current-people'),
        congestionStatus: document.getElementById('congestion-status'),
        populationCount: document.getElementById('population-count'),
        congestionSteps: document.getElementById('congestion-steps'),
        
        // 대시보드
        dashboardCount: document.getElementById('current-count'),
        dashboardStatus: document.getElementById('current-status'),
        dashboardWait: document.getElementById('wait-time')
    };

    // 대기 시간 계산
    function calculateWaitTime(label) {
        const waitTimes = {
            "원활": "즉시",
            "보통": "2-5분",
            "혼잡": "5-10분",
            "매우 혼잡": "10분+"
        };
        return waitTimes[label] || "측정중";
    }

    // 모든 UI 업데이트를 한 곳에서
    function updateAllUI(data) {
        const { level, object_count: count, label } = data;

        // 1. 막대 그래프 업데이트
        if (elements.bar) {
            elements.bar.setAttribute('data-level', level);
        }

        elements.vBars.forEach((vBar, index) => {
            vBar.setAttribute('data-active', index < level ? 'true' : 'false');
        });

        // 2. 기본 정보 업데이트
        if (elements.currentPeople) elements.currentPeople.textContent = `${count}명`;
        if (elements.congestionStatus) elements.congestionStatus.textContent = label;
        if (elements.populationCount) elements.populationCount.textContent = `${count}명`;
        if (elements.congestionSteps) elements.congestionSteps.textContent = label;

        // 3. 대시보드 업데이트
        if (elements.dashboardCount) elements.dashboardCount.textContent = `${count}명`;
        if (elements.dashboardStatus) elements.dashboardStatus.textContent = label;
        if (elements.dashboardWait) elements.dashboardWait.textContent = calculateWaitTime(label);
    }

    // 에러 처리
    function handleError(error) {
        console.error('혼잡도 데이터 로딩 실패:', error);
        
        const errorText = { count: '오류', status: '알 수 없음', wait: '-' };
        
        if (elements.currentPeople) elements.currentPeople.textContent = errorText.count;
        if (elements.congestionStatus) elements.congestionStatus.textContent = errorText.status;
        if (elements.populationCount) elements.populationCount.textContent = errorText.count;
        if (elements.congestionSteps) elements.congestionSteps.textContent = errorText.status;
        if (elements.dashboardCount) elements.dashboardCount.textContent = '-';
        if (elements.dashboardStatus) elements.dashboardStatus.textContent = errorText.status;
        if (elements.dashboardWait) elements.dashboardWait.textContent = errorText.wait;
    }

    // API 호출
    async function fetchAndUpdate() {
        try {
            const response = await fetch(config.apiUrl);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            updateAllUI(data);
        } catch (error) {
            handleError(error);
        }
    }

    // 초기 실행 및 주기적 업데이트
    fetchAndUpdate();
    setInterval(fetchAndUpdate, config.updateInterval);
})();

// ===================================================
// 5. 모바일 앱 스타일 네비게이션 & 뷰 전환
// ===================================================
(function setupAppNavigation() {
    const homeTab = document.getElementById('home-tab');
    const videoBtn = document.getElementById('video-view-btn');
    const populationBtn = document.getElementById('population-view-btn');
    
    const homeView = document.getElementById('home-view');
    const videoView = document.getElementById('video-view');
    const populationView = document.getElementById('population-view');
    
    const infoPanel = document.querySelector('.info-panel');
    const imagArea = document.querySelector('.imag-area');
    
    const allTabs = [homeTab, videoBtn, populationBtn];
    
    function activateTab(activeTab) {
        allTabs.forEach(tab => {
            if (tab) tab.classList.remove('active');
        });
        if (activeTab) activeTab.classList.add('active');
    }
    
    function switchView(viewType) {
        // 모든 뷰 숨기기
        if (infoPanel) {
            infoPanel.classList.remove('active');
            infoPanel.style.display = 'none';
        }
        if (imagArea) {
            imagArea.classList.remove('active');
            imagArea.style.display = 'none';
        }
        if (videoView) videoView.classList.remove('active');
        if (populationView) populationView.classList.remove('active');
        
        switch(viewType) {
            case 'home':
                if (infoPanel) {
                    infoPanel.classList.add('active');
                    infoPanel.style.display = 'block';
                }
                activateTab(homeTab);
                break;
                
            case 'population':
                if (imagArea) {
                    imagArea.classList.add('active');
                    imagArea.style.display = 'flex';
                }
                if (populationView) populationView.classList.add('active');
                activateTab(populationBtn);
                break;
                
            case 'video':
                if (imagArea) {
                    imagArea.classList.add('active');
                    imagArea.style.display = 'flex';
                }
                if (videoView) videoView.classList.add('active');
                activateTab(videoBtn);
                break;
        }
    }
    
    if (homeTab) {
        homeTab.addEventListener('click', (e) => {
            e.preventDefault();
            switchView('home');
        });
    }
    
    if (populationBtn) {
        populationBtn.addEventListener('click', (e) => {
            e.preventDefault();
            switchView('population');
        });
    }
    
    if (videoBtn) {
        videoBtn.addEventListener('click', (e) => {
            e.preventDefault();
            switchView('video');
        });
    }
    
    switchView('home');
})();


// ===================================================
// 6. 터치 제스처 지원
// ===================================================
(function setupTouchGestures() {
    const imagArea = document.querySelector('.imag-area');
    if (!imagArea) return;
    
    let touchStartX = 0;
    let touchEndX = 0;
    
    function handleSwipe() {
        const swipeThreshold = 50;
        const diff = touchEndX - touchStartX;
        
        if (Math.abs(diff) > swipeThreshold) {
            const videoView = document.getElementById('video-view');
            const populationView = document.getElementById('population-view');
            const videoBtn = document.getElementById('video-view-btn');
            const populationBtn = document.getElementById('population-view-btn');
            
            if (diff > 0) {
                if (videoView && videoView.classList.contains('active')) {
                    populationBtn.click();
                }
            } else {
                if (populationView && populationView.classList.contains('active')) {
                    videoBtn.click();
                }
            }
        }
    }
    
    imagArea.addEventListener('touchstart', (e) => {
        touchStartX = e.changedTouches[0].screenX;
    });
    
    imagArea.addEventListener('touchend', (e) => {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    });
})();


(function setupProcessorStatusMonitor() {
    function updateProcessorStatus() {
        fetch('/stream/video/check-processor/')
            .then(response => response.json())
            .then(data => {
                const badge = document.querySelector('.live-badge');
                if (!badge) return;
                
                const statusText = badge.querySelector('.status-text');
                if (!statusText) return;
                
                if (data.status === "실시간 모니터링 중") {
                    badge.classList.add('active');
                    badge.classList.remove('standby');
                } else {
                    badge.classList.add('standby');
                    badge.classList.remove('active');
                }
                
                statusText.textContent = data.status;
            })
            .catch(error => console.error('상태 확인 실패:', error));
    }
    
    updateProcessorStatus();
    setInterval(updateProcessorStatus, 10000);
})();


// prediction-ui.js
(function setupPredictionUI() {
    const API_URL = '/stream/api/predictions/';
    const UPDATE_INTERVAL = 10000; // 10초마다 업데이트

    // DOM 요소
    const elements = {
        // 추천 시간 카드
        recommendedTime: document.querySelector('.time-highlight'),
        recommendedWait: document.querySelector('.recommend-content p:last-child'),
        
        // 시간대별 슬롯
        timeSlots: document.querySelectorAll('.time-slot')
    };

    // 예측 데이터 가져오기
    async function fetchPredictions() {
        try {
            const response = await fetch(API_URL);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            
            console.log('📊 예측 데이터:', data);
            
            // UI 업데이트
            updateRecommendedTime(data.predictions);
            updateTimeSlots(data.predictions);
            
        } catch (error) {
            console.error('예측 데이터 로딩 실패:', error);
        }
    }

    // 1. 추천 시간 업데이트 (가장 덜 혼잡한 시간 찾기)
    function updateRecommendedTime(predictions) {
        if (!predictions || predictions.length === 0) {
            console.warn("추천 시간 업데이트 실패: 예측 데이터가 없습니다.");
            return;
        }

        // 1. 가장 낮은 레벨(가장 한가한) 예측 찾기
        const bestPrediction = predictions.reduce((best, current) => {
            return current.level < best.level ? current : best;
        });

        // 2. 'bestPrediction'에서 'seconds_ahead' 값을 가져옴
        const secondsAhead = bestPrediction.seconds_ahead;
        let timeText = "";

        // 3. '초'를 '분' 또는 '초' 텍스트로 변환
        if (secondsAhead < 60) {
            // 60초 미만이면 "N초 후"로 표시
            timeText = `약 ${secondsAhead}초 후`;
        } else {
            // 60초 이상이면 "N분 후"로 표시
            const minutesAhead = Math.round(secondsAhead / 60);
            if (minutesAhead === 0) {
                timeText = "지금"; // 0분에 매우 가까울 경우
            } else {
                timeText = `약 ${minutesAhead}분 후`;
            }
        }
        
        const waitTime = calculateWaitTime(bestPrediction.level);
        
        if (elements.recommendedTime) {
            elements.recommendedTime.textContent = timeText;
        }
        if (elements.recommendedWait) {
            elements.recommendedWait.textContent = `예상 대기시간 ${waitTime}`;
        }
    }

    // 2. 시간대별 슬롯 업데이트
    function updateTimeSlots(predictions) {
        if (!predictions || predictions.length === 0) return;
        const now = new Date();
        
        predictions.forEach((pred, index) => {
            if (index >= elements.timeSlots.length) return;

            const slot = elements.timeSlots[index];

            // (수정됨) V2 모델은 'seconds_ahead'를 반환합니다.
            // 'minutes_ahead * 60000' (분 -> 밀리초) 대신
            // 'seconds_ahead * 1000' (초 -> 밀리초)를 사용합니다.
            const futureTime = new Date(now.getTime() + pred.seconds_ahead * 1000);
            const hours = futureTime.getHours().toString().padStart(2, '0');
            const minutes = futureTime.getMinutes().toString().padStart(2, '0');
            const seconds = futureTime.getSeconds().toString().padStart(2, '0'); // <-- [수정됨] 초 추가

            // 시간 업데이트
            const timeEl = slot.querySelector('.time');
            if (timeEl) {
                timeEl.textContent = `${hours}:${minutes}:${seconds}`; // <-- [수정됨] 초 표시
            }
            
            // 혼잡도 바 업데이트
            const dots = slot.querySelectorAll('.congestion-dot');
            dots.forEach((dot, dotIndex) => {
                if (dotIndex < pred.level) {
                    dot.classList.add('active');
                } else {
                    dot.classList.remove('active');
                }
            });
            
            // 상태 레이블 업데이트
            const statusEl = slot.querySelector('.status');
            if (statusEl) {
                statusEl.textContent = pred.label;
                
                // 상태에 따른 색상 클래스 추가
                statusEl.className = 'status';
                if (pred.level >= 3) {
                    statusEl.classList.add('status-busy');
                } else if (pred.level <= 2) {
                    statusEl.classList.add('status-free');
                }
            }

            // 신뢰도 표시 (선택사항)
            if (pred.confidence) {
                slot.setAttribute('data-confidence', pred.confidence);
                slot.title = `신뢰도: ${pred.confidence}%`;
            }
        });
    }

    // 대기 시간 계산 헬퍼
    function    calculateWaitTime(level) {
        const waitTimes = {
            1: '1-2분',
            2: '2-5분',
            3: '5-10분',
            4: '10분 이상'
        };
        return waitTimes[level] || '측정 중';
    }

    // 초기 로드 및 주기적 업데이트
    fetchPredictions();
    setInterval(fetchPredictions, UPDATE_INTERVAL);

    // 디버깅용 - 수동 새로고침 버튼 추가 (선택사항)
    window.refreshPredictions = fetchPredictions;
})();