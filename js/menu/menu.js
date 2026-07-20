import { CATEGORY_ORDER } from "../config/constants.js";

import { createMenuCard } from "./card.js";

import {
    createNavigation,
    initNavigationObserver
} from "./navigation.js";

import {
    isAvailable,
    toPrice
} from "../utils/utils.js";

// ===========================
// Group
// ===========================

function groupByCategory(data) {

    const grouped = {};

    data.forEach(item => {

        const category = item["종류"];

        if (!grouped[category]) {
            grouped[category] = [];
        }

        grouped[category].push(item);

    });

    return grouped;

}

// ===========================
// Sort
// ===========================

function sortCategory(items) {

    items.sort((a, b) => {

        const availableA = isAvailable(a["판매 여부"]);
        const availableB = isAvailable(b["판매 여부"]);

        // 판매중 먼저
        if (availableA !== availableB) {
            return availableA ? -1 : 1;
        }

        // 가격순
        const priceA = toPrice(a["가격"]);
        const priceB = toPrice(b["가격"]);

        if (priceA !== priceB) {
            return priceA - priceB;
        }

        // 정렬값
        return (
            (Number(a["정렬"]) || 9999) -
            (Number(b["정렬"]) || 9999)
        );

    });

}

// ===========================
// Category Section
// ===========================

function createCategorySection(category) {

    const section = document.createElement("section");

    section.className = "category";
    section.id = `category-${category}`;

    section.innerHTML = `
        <h2>${category}</h2>
    `;

    return section;

}

// ===========================
// Menu
// ===========================

export function showMenu(data) {

    const menu = document.getElementById("menu");

    menu.innerHTML = "";

    const grouped = groupByCategory(data);

    const categories = CATEGORY_ORDER.filter(
        category => grouped[category]
    );

    createNavigation(categories);

    categories.forEach(category => {

        sortCategory(grouped[category]);

        const section = createCategorySection(category);

        grouped[category].forEach(item => {

            section.appendChild(
                createMenuCard(item, category)
            );

        });

        menu.appendChild(section);

    });

    initNavigationObserver();

}
