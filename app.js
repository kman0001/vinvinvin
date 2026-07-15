const API = "https://script.google.com/macros/s/AKfycbxrynnbzob7qwRG2wPzpyWbNAy4ZSxpvTiK0s3uFBFUcwjDg5PZbfBKaiWHIZ8W__mIJg/exec";

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
        "칠레": "🇨🇱",
        "미국": "🇺🇸",
        "호주": "🇦🇺",
        "뉴질랜드": "🇳🇿",
        "독일": "🇩🇪",
        "포르투갈": "🇵🇹",
        "아르헨티나": "🇦🇷",
        "벨기에": "🇧🇪",
        "네덜란드": "🇳🇱",
        "스코틀랜드": "🏴",
        "일본": "🇯🇵"
    };

    return flags[country] || "🍷";
}

function showNotice(data){

    const notice=document.getElementById("notice");

    if(!notice || !data.length) return;

    data.sort((a,b)=>
        Number(a["정렬"])-Number(b["정렬"])
    );

    const title =
        data.find(v=>v["항목"]==="제목")?.["내용"] || "안내";

    const guides =
        data.filter(v=>v["항목"]==="안내");

    const warnings =
        data.filter(v=>v["항목"]==="주의");

    const warnings =
        data.filter(v=>v["항목"]==="이벤트");
    
    const warnings =
        data.filter(v=>v["항목"]==="기타");
    
    let html = `
        <div class="notice-box">

            <div class="notice-title">${title}</div>

            <ul class="notice-list">
    `;

    guides.forEach(item=>{

        html += `<li>• ${item["내용"]}</li>`;

    });

    html += `</ul>`;

    if(warnings.length){

        html += `

            <div class="notice-warning">

                <h3>⚠️ 주의</h3>

                <ul class="notice-list">
        `;

        warnings.forEach(item=>{

            html += `<li>${item["내용"]}</li>`;

        });

        html += `</ul></div>`;

    }

    html += `</div>`;

    notice.innerHTML = html;

}

function showMenu(data) {

    const menu = document.getElementById("menu");
    const nav = document.getElementById("category-nav");

    menu.innerHTML = "";
    nav.innerHTML = "";

    const categoryOrder = [
        "잔와인",
        "레드",
        "화이트",
        "스파클링",
        "맥주",
        "위스키",
        "꼬냑"
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

            const printDesc = item["설명 (인쇄용)"] || "";
            const webDesc = item["설명 (웹용)"] || "";
            const price = Number(item["가격"]) || 0;

            const recommended =
                String(item["추천"]).toUpperCase() === "TRUE";

            const available =
                String(item["판매 여부"]).toUpperCase() !== "FALSE";

            // 설명 분리
            const info = printDesc.split("/").map(v => v.trim());

            const country = info[0] || "";
            const grape = info[1] || "";
            const abv = info[2] || "";
            const extra = info[3] || "";

            const flag = getFlag(country);

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

                            ${grape ? `<span class="tag">🍇 ${grape}</span>` : ""}

                            ${abv ? `<span class="tag">🍷 ${abv}</span>` : ""}

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
    
        const observer = new IntersectionObserver((entries) => {
    
            entries.forEach(entry => {
    
                if (!entry.isIntersecting) return;
    
                const id = entry.target.id.replace("category-", "");
    
                navButtons.forEach(button => {
    
                    button.classList.toggle(
                        "active",
                        button.dataset.category === id
                    );
    
                });
    
            });
    
        }, {
            root: null,
            rootMargin: "-25% 0px -60% 0px",
            threshold: 0
        });
    
        sections.forEach(section => observer.observe(section));

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
