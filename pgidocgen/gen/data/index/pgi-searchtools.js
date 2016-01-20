// Utils ------------------------

/** Returns whether `str` starts with `suffix` */
function endsWith(str, suffix) {
    return str.indexOf(suffix, str.length - suffix.length) !== -1;
}

/** Returns how ofter `s1` occurs in `str` */
function count(str, s1) {
    return (str.length - str.replace(new RegExp(s1,"g"), '').length) / s1.length;
}

/** Asserts the condition and throws `message` if it's not true */
function assert(condition, message) {
    if (!condition) {
        throw message || "Assertion failed";
    }
}

/** Sort function using default operators */
function cmp(x, y) {
        return x > y? 1 : x < y ? -1 : 0;
}

/** Returns a list of object values, similar to Object.keys() */
function objectValues(obj) {
    var values = [];
    var keys = Object.keys(obj);
    for (var i=0; i < keys.length; i++)
        values.push(obj[keys[i]]);
    return values;
}

// SearchResults ------------------------

/**
 * Creates a new SearchResults object.
 * @class
 */
SearchResults = function(id) {
    this._obj = $(document.getElementById(id));
    this._original = this._obj.html();
    this._current_id = 0;
}

/**
 * Stops any currently occurring fill operation
 */
SearchResults.prototype.abortFill = function() {
    this._current_id++;
}

/**
 * Hide the search results and restores the original list
 */
SearchResults.prototype.hide = function() {
    this.abortFill();
    this._obj.html(this._original);
}

/**
 * Fills the results list with the provided results.
 * `show_max` is the number or entries shown in the end (-1 means unlimited)
 * `show_first` is the number which will be inserted immediately (-1 means all)
 */
SearchResults.prototype.fill = function(results, show_max, show_first) {
    assert(show_first <= show_max);

    var not_shown = 0;

    this.abortFill();

    if (results.length > show_max && show_max != -1) {
        not_shown = results.length - show_max;
        results = results.slice(results.length - show_max, results.length);
    }

    var that = this;

    function displayNextItem(current_id, entry_index) {
        if (current_id !== that._current_id)
            return;

        if (!results.length) {
            if (not_shown > 0)
                that.appendMessage("and " + not_shown + " more...");
            return;
        }

        var item = results.pop();
        var listItem = $('<li style="display:none"></li>');
        var a = $('<a/>').attr('href',
            item[0] + ".html" +
            item[3]).attr('target', 'Content').attr("title", item[1]);
        a.append($('<div/>').attr("class", "right").html(item[2]));
        a.append($('<div/>').attr("class", "left").html(item[1]));
        listItem.append(a);
        that._obj.append(listItem);

        // show the first `entry_index` immediately, then delay updates
        if (entry_index <= show_first || show_first == -1) {
            listItem.show();
            displayNextItem(current_id, entry_index + 1);
        } else {
            listItem.slideDown(5, function() {
                displayNextItem(current_id, entry_index + 1);
            });
        }
    }

    this._obj.empty();
    if (!results.length)
        that.showMessage("No Results");
    else
        displayNextItem(this._current_id, 0);
}

/**
 * Clears the result list and shows a status message
 */
SearchResults.prototype.showMessage = function(text) {
    this._obj.empty();
    this.appendMessage(text);
}

/**
 * Shows a status message at the end of the current list
 */
SearchResults.prototype.appendMessage = function(text) {
    var listItem = $('<li></li>');
    listItem.append($('<a/>').attr('class', 'message').html(text));
    this._obj.append(listItem);
}


// SearchIndex ------------------------

/**
 * Creates a new SearchIndex
 * @class
 */
SearchIndex = function() {
    this._results = new SearchResults('search-results');
    this._index = null;

    this._queued_query = null;
    this._active_query = null;
}

/** Load the search index located at `url`. Pass an ID for an empty script tag
 * as `target_id`.
 */
SearchIndex.prototype.loadIndex = function(url, target_id) {
    $.ajax({type: "GET", url: url, data: null,
            dataType: "script", cache: true,
            complete: function(jqxhr, textstatus) {
              if (textstatus != "success") {
                document.getElementById(target_id).src = url;
              }
            }});
}

/**
 * This gets called by the loaded search index. After the index is set
 * any queued queries are executed.
 */
SearchIndex.prototype.setIndex = function(index) {
    assert(this._index === null);

    this._index = index;
    if ((q = this._queued_query) !== null) {
      this._queued_query = null;
      this._query(q);
    }
}

/**
 * Start a search. Any active search will be aborted and a new one queued.
 * This also works before the search index is loaded.
 */
SearchIndex.prototype.performSearch = function(query) {
    if (query == this._active_query)
        return;
    this._active_query = query;

    this.abortSearch();
    window.scrollTo(0, 0);

    if (this._index !== null)
        this._query(query);
    else {
        this._results.showMessage("Loading Search Index...");
        this._queued_query = query;
    }
}

/**
 * Abort the search. This should be followed by an performSearch() otherwise
 * the search is in an inconsistent state
 */
SearchIndex.prototype.abortSearch = function() {
    this._results.abortFill();
}

/**
 * Starts the actual search. Needs an index already set.
 */
SearchIndex.prototype._query = function(query) {
    assert(this._index !== null);

    var parts = query.split(/\s+/);
    // filter out empty ones
    parts = parts.filter(function(e){return e});

    var max_entries = 200;
    var show_first = 30;
    var results = [];

    if(!parts.length) {
        this._results.hide();
        return;
    }

    // array of [filename, title, anchor, score]
    results = this._getResults(parts);

    // now sort the results by score (in opposite order of appearance, since the
    // display function below uses pop() to retrieve items) and then
    // alphabetically
    results.sort(function(a, b) {
      var left = a[4];
      var right = b[4];
      if (left > right) {
        return 1;
      } else if (left < right) {
        return -1;
      } else {
        // same score: sort alphabetically
        left = a[1].toLowerCase();
        right = b[1].toLowerCase();
        return (left > right) ? -1 : ((left < right) ? 1 : 0);
      }
    });

    this._results.fill(results, max_entries, show_first);
}

/**
 * Returns the namespace objects to search in
 */
SearchIndex.prototype._getNamespaces = function() {
    assert(this._index !== null);

    var index = this._index;
    var ns_keys = Object.keys(index.namespaces);

    var get_name = function(text) {
        var res = text.split("-");
        return res[0];
    };

    var sort_key = function(text) {
        var res = text.split("-");
        var name = res[0];
        var version = res[1];
        var vparts = version.split(".");
        vparts = vparts.map(function (x) {
            return parseInt(x, 10);
        });
        return [name, vparts];
    };

    var include_all = PGIConfig.getIncludeAll();
    var namespaces = {}

    if (include_all) {
        // only select the newest one; sort by name and version and hash by name
        // in that order
        ns_keys.sort(function(a, b) {
            return cmp(sort_key(a), sort_key(b));
        });

        var result = {}
        for(var i=0; i < ns_keys.length; i++) {
            var ns = ns_keys[i];
            var name = get_name(ns);
            result[name] = ns;
        }

        for (var name in result) {
            var ns = result[name];
            namespaces[ns] = index.namespaces[ns];
        }
    } else {
        var include_modules = PGIConfig.getModules();

        for(var i=0; i < ns_keys.length; i++) {
            var ns = ns_keys[i];
            if (include_modules.indexOf(ns) >= 0)
                namespaces[ns] = index.namespaces[ns];
        }
    }

    return namespaces;
}

/**
 * Given a search term list returns a list of unsorted results from the index.
 */
SearchIndex.prototype._getResults = function(parts) {
    assert(this._index !== null);

    var index = this._index;
    var objnames = index.objnames;
    var namespaces = this._getNamespaces();

    var results = [];
    var case_insensitive = PGIConfig.getCaseInsensitive();

    var do_score = function (text, part) {
        // returns -1 if not found, or a score >= 0

        var lower_text;
        var lower_part;

        if (!case_insensitive) {
            lower_text = text;
            lower_part = part;
        } else {
            lower_text = text.toLowerCase();
            lower_part = part.toLowerCase();
        }

        var index = lower_text.indexOf(lower_part);

        // it's not in there
        if(index == -1)
            return -1;

        // prefer more matching text
        var lower_count = lower_text.split(lower_part).length - 1;
        score = (lower_count * part.length) / text.length;

        // get the character right before the match
        var prev;
        if (index == 0)
            prev = ""
        else
            prev = lower_text[index - 1];

        // prefer when it starts a part, preferring start, "." and ":"
        if (prev == "." || prev == ":"  || prev == "")
            score *= 3;
        else if (prev == "-" || prev == "_")
            score *= 2;

        return score;
    };

    for (var ns in namespaces) {
        var namespace = namespaces[ns];
        var objects = namespace.objects;
        var titles = namespace.titles;
        var filenames = namespace.filenames;
        var module = ns.split("-")[0];
        var partsLength = parts.length;

        var get_fn = function(index) {
            return ns + "/" + filenames[index];
        };

        var titleLength = titles.length;
        for (var i = 0; i < titleLength; i++) {
            var title = titles[i];
            var version = "";

            // strip away the library version
            if(title.indexOf(" (") != -1) {
                version = title.slice(title.indexOf(" (") + 2, title.length - 1);
                title = title.slice(0, title.indexOf(" ("));
            }

            var all_score = 0;
            for(var j = 0; j < partsLength; j++) {
                var part = parts[j];
                var score = do_score(title, part);
                if(score < 0) {
                    all_score = -1;
                    break;
                } else {
                    all_score += score;
                }
            }

            if(all_score >= 0) {
                var type_name;
                var filename = get_fn(i);
                if (endsWith(filename, "index") && count(filename, "/") < 2) {
                    // this is the title page of each module..
                    // try to make it the first match
                    all_score += 100;
                    type_name = version || "module";
                } else {
                    // all other titles get shown last, thus -100
                    all_score -= 100;
                    type_name = "page";
                }

                results.push([
                    filename, title, type_name,
                    '', all_score]);
            }
        }

        for (var prefix in objects) {
            for (var name in objects[prefix]) {
                var fullname = module + "." + (prefix ? prefix + '.' : '') + name;

                var all_score = 0;
                for(var j = 0; j < partsLength; j++) {
                    var part = parts[j];
                    var score = do_score(fullname, part);
                    if(score < 0) {
                        all_score = -1;
                        break;
                    } else {
                        all_score += score;
                    }
                }

                if(all_score >= 0) {
                    var match = objects[prefix][name];
                    var type_name = objnames[match[1]][1];
                    var filename = get_fn(match[0]);
                    var anchor = match[3];

                    if (anchor == "")
                        anchor = fullname;
                    else
                        anchor = module + "." + anchor;

                    results.push([
                        filename,
                        fullname, type_name,
                        '#' + anchor, all_score]);
                }
            }
        }
    }

    return results;
}
