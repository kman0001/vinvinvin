// ===========================
// Constants
// ===========================

const LANG = {
  KO: "ko"
};

const SHEETS = {
  MENU: "메뉴판",
  NOTICE: "안내"
};

const CACHE_EXPIRATION = 21600;        // CacheService TTL (6시간)
const CACHE_REFRESH_TIME = 21000000;   // 강제 재생성 기준 (5시간 50분)
const CACHE_SIZE_LIMIT = 90000;        // 90KB


const PROP_LAST_EDIT = "last_sheet_edit";
const PROP_CACHE_ERROR = "last_cache_error";


// ===========================
// Image
// ===========================

function convertDriveImageUrl(url) {

  if (typeof url !== "string") {
    return url;
  }


  const patterns = [
    /\/file\/d\/([a-zA-Z0-9_-]+)/,
    /[?&]id=([a-zA-Z0-9_-]+)/
  ];


  for (const pattern of patterns) {

    const match = url.match(pattern);

    if (match) {
      return `https://drive.google.com/uc?export=view&id=${match[1]}`;
    }
  }


  return url;
}


// ===========================
// Sheet
// ===========================

function getSheetData(spreadsheet, sheetName) {

  const sheet =
    spreadsheet.getSheetByName(sheetName);


  if (!sheet) {
    return [];
  }


  const values =
    sheet.getDataRange().getValues();


  if (values.length <= 1) {
    return [];
  }


  const headers =
    values.shift()
      .map(header =>
        String(header)
          .replace(/\t/g, "")
          .trim()
      );


  return values.map(row => {

    const obj = {};


    headers.forEach((header, index) => {

      let value = row[index];


      if (header === "사진") {
        value = convertDriveImageUrl(value);
      }


      obj[header] = value;

    });


    return obj;

  });
}


// ===========================
// Cache
// ===========================

function getCacheStore() {
  return CacheService.getScriptCache();
}


function saveCacheError(message) {

  PropertiesService
    .getScriptProperties()
    .setProperty(
      PROP_CACHE_ERROR,
      `${new Date().toISOString()} ${message}`
    );
}

function checkCacheError() {

  const error =
    PropertiesService
      .getScriptProperties()
      .getProperty(
        PROP_CACHE_ERROR
      );


  console.log(
    error || "No cache error"
  );

}

function checkCacheStatus() {

  const props =
    PropertiesService
      .getScriptProperties();


  const lastSheetEdit =
    Number(
      props.getProperty(PROP_LAST_EDIT)
    ) || 0;


  const cache =
    getCacheStore()
      .get(`cache_${LANG.KO}`);


  if (!cache) {
    console.log("Cache: 없음");
    return;
  }


  const cached =
    JSON.parse(cache);


  const age =
    Date.now() - cached.createdAt;


  const expired =
    age >= CACHE_REFRESH_TIME;


  console.log(
    "Sheet last edit:",
    new Date(lastSheetEdit)
  );


  console.log(
    "Cache created:",
    new Date(cached.createdAt)
  );


  console.log(
    "Cache sheet version:",
    new Date(cached.sheetUpdatedAt)
  );


  console.log(
    "Cache age:",
    Math.floor(age / 1000),
    "seconds"
  );


  console.log(
    "Cache expired:",
    expired
  );


  console.log(
    "Cache valid:",
    cached.sheetUpdatedAt === lastSheetEdit && !expired
  );

}

function getLastSheetEdit() {

  return Number(
    PropertiesService
      .getScriptProperties()
      .getProperty(PROP_LAST_EDIT)
  ) || 0;

}


function getCachedResponse(lang) {

  const cache =
    getCacheStore();


  const json =
    cache.get(
      `cache_${lang}`
    );


  if (!json) {
    return null;
  }


  const cached =
    JSON.parse(json);


  const lastEdit =
    getLastSheetEdit();


  const expired =
    Date.now() - cached.createdAt
      >= CACHE_REFRESH_TIME;


  if (
    cached.sheetUpdatedAt !== lastEdit ||
    expired
  ) {
    return null;
  }


  return JSON.stringify({
    lang: lang,
    ...cached.data
  });

}


function setCachedResponse(lang, data) {

  const payload = {

    createdAt: Date.now(),

    sheetUpdatedAt:
      getLastSheetEdit(),

    data: data

  };


  const json =
    JSON.stringify(payload);


  const size =
    Utilities
      .newBlob(json)
      .getBytes()
      .length;


  if (size > CACHE_SIZE_LIMIT) {

    saveCacheError(
      `Cache too large: cache_${lang} (${size} bytes)`
    );

    return false;
  }


  try {

    getCacheStore()
      .put(
        `cache_${lang}`,
        json,
        CACHE_EXPIRATION
      );


    return true;


  } catch (error) {

    saveCacheError(
      `Cache write failed: ${error.message}`
    );


    return false;

  }

}


// ===========================
// Response
// ===========================

function getResponseJson(lang) {

  const lock =
    LockService.getScriptLock();


  try {

    lock.waitLock(10000);


    const cached =
      getCachedResponse(lang);


    if (cached !== null) {
      return cached;
    }


    const spreadsheet =
      SpreadsheetApp
        .getActiveSpreadsheet();


    const data = {

      menu:
        getSheetData(
          spreadsheet,
          SHEETS.MENU
        ),


      notice:
        getSheetData(
          spreadsheet,
          SHEETS.NOTICE
        )

    };


    setCachedResponse(
      lang,
      data
    );


    return JSON.stringify({

      lang: lang,

      ...data

    });


  } finally {

    lock.releaseLock();

  }

}


// ===========================
// API
// ===========================

function doGet(e) {

  const lang =
    (
      e &&
      e.parameter &&
      e.parameter.lang
    )
    || LANG.KO;


  return ContentService
    .createTextOutput(
      getResponseJson(lang)
    )
    .setMimeType(
      ContentService.MimeType.JSON
    );

}


// ===========================
// Trigger
// ===========================

function onSheetEdit(e) {

  if (!e || !e.range) {
    return;
  }


  const sheetName =
    e.range
      .getSheet()
      .getName();


  const WATCH_SHEETS = [
    SHEETS.MENU,
    SHEETS.NOTICE,
    "단가표"
  ];


  if (!WATCH_SHEETS.includes(sheetName)) {
    return;
  }


  PropertiesService
    .getScriptProperties()
    .setProperty(
      PROP_LAST_EDIT,
      Date.now().toString()
    );

}
