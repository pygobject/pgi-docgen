/**
 * @param {string} value
 * @returns {boolean}
 */
function parseBoolean(value) {
  return value === "true";
}

/**
 * @param {string} key
 * @param {string} defaultValue
 * @returns {string}
 */
function getStorageItem(key, defaultValue) {
  const value = localStorage.getItem(key);
  return value !== null ? value : defaultValue;
}

class Config {
  reset() {
    localStorage.removeItem("case_insensitive");
    localStorage.removeItem("include_all");
    localStorage.removeItem("search_modules");
  }

  /**
   * @param {boolean} value
   */
  setCaseInsensitive(value) {
    localStorage.setItem("case_insensitive", String(value));
  }

  /**
   * @returns {boolean}
   */
  getCaseInsensitive() {
    return parseBoolean(getStorageItem("case_insensitive", "true"));
  }

  /**
   * @param {boolean} value
   */
  setIncludeAll(value) {
    localStorage.setItem("include_all", String(value));
  }

  /**
   * @returns {boolean}
   */
  getIncludeAll() {
    return parseBoolean(getStorageItem("include_all", "true"));
  }

  /**
   * @param {string[]} modules
   */
  setModules(modules) {
    localStorage.setItem("search_modules", modules.join(","));
  }

  /**
   * @returns {string[]}
   */
  getModules() {
    const result = getStorageItem("search_modules", "");
    if (result === "") return [];
    return result.split(",");
  }
}

const PGIConfig = new Config();
