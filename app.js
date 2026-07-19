const API = "https://script.google.com/macros/s/AKfycbxRjcOBvaZJwDWYkMLie7rZfEA91YTruX9b2r2gC6xNm6ogN9xbo9rZ-L-hcTS-drFMYA/exec";

fetch(API)
    .then(response => response.json())
    .then(data => {

        showNotice(data.notice);

        showMenu(data.menu);

    })
    .catch(error => {

        console.error(error);

        document.getElementById("menu").innerHTML =
            "<p>메뉴를 불러오지 못했습니다.</p>";

    });

function getFlag(country) {
    const flags = {
        "이탈리아": "🇮🇹",
        "프랑스": "🇫🇷",
        "스페인": "🇪🇸",
        "포르투갈": "🇵🇹",
        "독일": "🇩🇪",
        "오스트리아": "🇦🇹",
        "헝가리": "🇭🇺",
        "그리스": "🇬🇷",
        "조지아": "🇬🇪",

        "미국": "🇺🇸",
        "캐나다": "🇨🇦",
        "멕시코": "🇲🇽",

        "칠레": "🇨🇱",
        "아르헨티나": "🇦🇷",
        "우루과이": "🇺🇾",
        "브라질": "🇧🇷",

        "호주": "🇦🇺",
        "뉴질랜드": "🇳🇿",
        "남아프리카공화국": "🇿🇦",
        "남아공": "🇿🇦",

        "일본": "🇯🇵",
        "중국": "🇨🇳",

        "영국": "🇬🇧",
        "잉글랜드": "🏴",
        "스코틀랜드": "🏴",
        "웨일스": "🏴",

        "벨기에": "🇧🇪",
        "네덜란드": "🇳🇱",
        "룩셈부르크": "🇱🇺",

        "슬로베니아": "🇸🇮",
        "크로아티아": "🇭🇷",
        "루마니아": "🇷🇴",
        "불가리아": "🇧🇬",
        "체코": "🇨🇿",
        "슬로바키아": "🇸🇰",
        "몰도바": "🇲🇩",

        "이스라엘": "🇮🇱",
        "레바논": "🇱🇧",
        "튀르키예": "🇹🇷",
        "터키": "🇹🇷"
    };

    return flags[country] || "🍷";
}

function getTypeIcon(category) {
    switch (category) {
        case "맥주":
            return "🍺";
        case "위스키":
        case "꼬냑":
            return "🥃";
        default:
            return "🍇";
    }
}

function showNotice(data){

    const notice = document.getElementById("notice");

    if(!notice || !data.length) return;

    data = data
        .filter(item => String(item["내용"]).trim() !== "")
        .sort((a,b)=>Number(a["정렬"])-Number(b["정렬"]));

    const title =
        data.find(v=>v["항목"]==="제목")?.["내용"] || "안내";

    let html = `
        <div class="notice-box">

            <div class="notice-title">${title}</div>
    `;

    const sections = [
        {
            type: "안내",
            title: "",
            icon: "•"
        },
        {
            type: "주의",
            title: "⚠️ 주의",
            icon: "•"
        },
        {
            type: "이벤트",
            title: "🎉 이벤트",
            icon: "•"
        },
        {
            type: "기타",
            title: "ℹ️ 기타",
            icon: "•"
        }
    ];

    sections.forEach(section => {

        const items = data.filter(v => v["항목"] === section.type);

        if(!items.length) return;

        if(section.title){
            html += `
                <div class="notice-warning">
                    <h3>${section.title}</h3>
                    <ul class="notice-list">
            `;
        }else{
            html += `<ul class="notice-list">`;
        }

        items.forEach(item=>{
            html += `<li>${section.icon} ${item["내용"]}</li>`;
        });

        html += `</ul>`;

        if(section.title){
            html += `</div>`;
        }

    });

    html += `</div>`;

    notice.innerHTML = html;

}

function showMenu(data) {

    const menu = document.getElementById("menu");
    const nav = document.getElementById("category-nav");

    menu.innerHTML = "";
    nav.innerHTML = "";

    const categoryOrder = [
        "글라스 와인",
        "레드",
        "화이트",
        "스파클링",
        "맥주",
        "위스키",
        "꼬냑",
        "안주"
    ];

    // 종류별 그룹화
    const grouped = {};

    data.forEach(item => {

        const category = item["종류"];

        if (!grouped[category]) {
            grouped[category] = [];
        }

        grouped[category].push(item);

    });

    // 카테고리 생성
    categoryOrder.forEach(category => {

        if (!grouped[category]) return;

        // 정렬
        grouped[category].sort((a, b) => {

            const availableA =
                String(a["판매 여부"]).toUpperCase() !== "FALSE";
        
            const availableB =
                String(b["판매 여부"]).toUpperCase() !== "FALSE";
        
            // 판매 중인 메뉴를 먼저 표시
            if (availableA !== availableB) {
                return availableA ? -1 : 1;
            }
        
            // 가격 오름차순
            const priceA = Number(a["가격"]) || 0;
            const priceB = Number(b["가격"]) || 0;
        
            if (priceA !== priceB) {
                return priceA - priceB;
            }
        
            // 가격이 같으면 기존 정렬값 사용
            const orderA = Number(a["정렬"]) || 9999;
            const orderB = Number(b["정렬"]) || 9999;
        
            return orderA - orderB;
        
        });

        // ==========================
        // Navigation Button
        // ==========================

        const button = document.createElement("button");

        button.className = "nav-button";
        button.textContent = category;
        button.dataset.category = category;

        button.onclick = () => {

            document
                .getElementById(`category-${category}`)
                .scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });

        };

        nav.appendChild(button);

        // ==========================
        // Section
        // ==========================

        const section = document.createElement("section");

        section.id = `category-${category}`;
        section.className = "category";

        section.innerHTML = `<h2>${category}</h2>`;

        // ==========================
        // Cards
        // ==========================

        grouped[category].forEach(item => {

            const card = document.createElement("div");
            card.className = "card";

            const imageFile = (item["사진"] || "").trim();

            const isExternal =
                /^(https?:)?\/\//i.test(imageFile);
            
            const imageSrc = isExternal
                ? imageFile
                : `images/${imageFile || "no-image.jpg"}`;

            const printDesc = item["주요 정보 1"] || "";
            const webDesc = item["설명"] || "";
            const price = Number(item["가격"]) || 0;

            const recommended =
                String(item["추천"]).toUpperCase() === "추천";

            const available =
                String(item["판매 여부"]).toUpperCase() !== "품절";

            // 설명 분리
            const info = printDesc.split("/").map(v => v.trim());

            const country = info[0] || "";
            const variety = info[1] || "";
            const abv = info[2] || "";
            const extra = info[3] || "";

            const flag = getFlag(country);
            const typeIcon = getTypeIcon(category);

            let extraIcon = "📌";

            if (/^\d{4}$/.test(extra) || extra.toUpperCase() === "NV") {
                extraIcon = "📅";
            } else if (/ml/i.test(extra)) {
                extraIcon = "🥂";
            }

            card.innerHTML = `

                <div class="card-layout">

                    <img
                        class="wine-image"
                        loading="lazy"
                        decoding="async"
                        data-image="${imageSrc}"
                        src="${imageSrc}"
                        alt="${item["이름"]}"
                        onerror="this.src='images/no-image.jpg'"
                    >

                    <div class="wine-info">

                        <div class="name">

                            ${item["이름"]}

                            ${
                                recommended
                                ? `<span class="badge">추천</span>`
                                : ""
                            }

                        </div>

                        <div class="wine-meta">

                            ${country ? `<span class="tag">${flag} ${country}</span>` : ""}

                            ${variety ? `<span class="tag">${typeIcon} ${variety}</span>` : ""}

                            ${abv ? `<span class="tag">☺️ ${abv}</span>` : ""}

                            ${extra ? `<span class="tag">${extraIcon} ${extra}</span>` : ""}

                        </div>

                        ${
                            webDesc
                                ? `<div class="web-desc">${webDesc}</div>`
                                : ""
                        }

                        <div class="price">

                            ${
                                available
                                    ? `₩${price.toLocaleString("ko-KR")}`
                                    : `<span class="soldout">SOLD OUT</span>`
                            }

                        </div>

                    </div>

                </div>

            `;

            section.appendChild(card);

        });

        menu.appendChild(section);

    });

        // ==========================
        // 현재 카테고리 활성화
        // ==========================
        
        const sections = document.querySelectorAll(".category");
        const navButtons = document.querySelectorAll(".nav-button");
        
        function updateActiveCategory() {
        
            const navHeight =
                document.getElementById("category-nav").offsetHeight;
        
            const scrollPosition =
                window.scrollY + navHeight + 30;
        
            let currentCategory = sections[0];
        
            sections.forEach(section => {
        
                if (section.offsetTop <= scrollPosition) {
                    currentCategory = section;
                }
        
            });
        
            navButtons.forEach(button => {
        
                button.classList.toggle(
                    "active",
                    button.dataset.category ===
                    currentCategory.id.replace("category-", "")
                );
        
            });
        
        }
        
        window.addEventListener("scroll", updateActiveCategory);
        
        window.addEventListener("resize", updateActiveCategory);
        
        updateActiveCategory();

        // ==========================
        // Lightbox
        // ==========================
        
        const lightbox = document.getElementById("lightbox");
        const lightboxImage = document.getElementById("lightbox-image");
        const closeButton = document.querySelector(".lightbox-close");
        
        document.querySelectorAll(".wine-image").forEach(image=>{
        
            image.addEventListener("click",()=>{
        
                lightboxImage.src=image.dataset.image;
        
                lightbox.classList.add("show");
        
            });
        
        });
        
        function closeLightbox(){
        
            lightbox.classList.remove("show");
        
            lightboxImage.src="";
        
        }
        
        closeButton.onclick=closeLightbox;
        
        lightbox.onclick=(e)=>{
        
            if(e.target===lightbox){
        
                closeLightbox();
        
            }
        
        };
        
        document.addEventListener("keydown",(e)=>{
        
            if(e.key==="Escape"){
        
                closeLightbox();
        
            }
        
        });

}

