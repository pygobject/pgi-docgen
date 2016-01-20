function parseBoolean(value) {
    return (/^true$/i).test(value);
}


function getCookie(key, def) {
    var value = Cookies.get(key);
    if (value === undefined)
        return def
    return value;
}


Config = function() {
}


Config.prototype.reset = function() {
    Cookies.remove('case_insensitive');
    Cookies.remove('include_all');
    Cookies.remove('search_modules');
}


Config.prototype.setCaseInsensitive = function(value) {
    Cookies.set('case_insensitive', String(value));
}


Config.prototype.getCaseInsensitive = function() {
    return parseBoolean(getCookie('case_insensitive', 'true'));
}


Config.prototype.setIncludeAll = function(value) {
    Cookies.set('include_all', String(value));
}


Config.prototype.getIncludeAll = function() {
    return parseBoolean(getCookie('include_all', 'true'));
}


Config.prototype.setModules = function(modules) {
    Cookies.set('search_modules', modules.join(","));
}


Config.prototype.getModules = function() {
    var result = getCookie('search_modules', '');
    if (result == '')
        return [];
    return result.split(",");
}


Config.prototype.getIncludeAll = function() {
    return parseBoolean(getCookie('include_all', 'true'));
}


var PGIConfig = new Config();
