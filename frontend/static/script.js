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
    setInterval(updateGraph, 5000);
})();


// ===================================================
// 4. 실시간 혼잡도 정보 업데이트 기능 (5초 주기)
// ===================================================
(function setupCongestionStatus() {
    const populationDiv = document.querySelector('.population-details');
    if (!populationDiv) return;

    const countElement = document.getElementById('population-count');
    const congestionElement = document.getElementById('congestion-steps');
    const iconElement = document.getElementById('density_Icon');
    
    // 대시보드 요소들
    const dashboardCount = document.getElementById('current-count');
    const dashboardStatus = document.getElementById('current-status');
    const dashboardWait = document.getElementById('wait-time');
    
    const apiUrl = populationDiv.dataset.url;

    if (!countElement || !congestionElement || !iconElement || !apiUrl) return;

    function updateIcon(label) {
        let newIconClass = '';
        let newColor = '';

        switch (label) {
            case "원활":
                newIconClass = 'fa-solid fa-face-grin-beam fa-8x';
                newColor = '#10b981';
                break;
            case "보통":
                newIconClass = 'fa-solid fa-face-meh fa-8x';
                newColor = '#f59e0b';
                break;
            case "혼잡":
                newIconClass = 'fa-solid fa-face-frown fa-8x';
                newColor = '#ef4444';
                break;
            case "매우 혼잡":
                newIconClass = 'fa-solid fa-face-dizzy fa-8x';
                newColor = '#dc2626';
                break;
            default:
                newIconClass = 'fa-solid fa-face-sad-tear fa-8x';
                newColor = '#8B5CF6';
                break;
        }
        iconElement.className = newIconClass;
        iconElement.style.color = newColor;
    }

    function calculateWaitTime(count, label) {
        // 혼잡도에 따른 예상 대기 시간 계산
        if (label === "원활") return "즉시";
        if (label === "보통") return "2-5분";
        if (label === "혼잡") return "5-10분";
        if (label === "매우 혼잡") return "10분+";
        return "측정중";
    }

    function updateStatus() {
        fetch(apiUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                const count = data.object_count;
                const label = data.label;
                
                // 인구 뷰 업데이트
                countElement.textContent = `${count}명`;
                congestionElement.textContent = label;
                updateIcon(label);
                
                // 대시보드 업데이트
                if (dashboardCount) dashboardCount.textContent = `${count}명`;
                if (dashboardStatus) dashboardStatus.textContent = label;
                if (dashboardWait) dashboardWait.textContent = calculateWaitTime(count, label);
            })
            .catch(error => {
                console.error('혼잡도 데이터를 불러오는 데 실패했습니다:', error);
                countElement.textContent = '오류';
                congestionElement.textContent = '알 수 없음';
                updateIcon('오류');
                
                if (dashboardCount) dashboardCount.textContent = '-';
                if (dashboardStatus) dashboardStatus.textContent = '오류';
                if (dashboardWait) dashboardWait.textContent = '-';
            });
    }

    updateStatus();
    setInterval(updateStatus, 5000);
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