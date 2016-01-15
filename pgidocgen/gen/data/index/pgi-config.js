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


Config.prototype.setCaseSensitive = function(value) {
    Cookies.set('case_sensitive', String(value));
}


Config.prototype.getCaseSensitive = function() {
    return parseBoolean(getCookie('case_sensitive', 'false'));
}


var PGIConfig = new Config();
