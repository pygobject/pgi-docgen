/*
 * searchtools.js_t
 * ~~~~~~~~~~~~~~~~
 *
 * Sphinx JavaScript utilties for the full-text search.
 *
 * :copyright: Copyright 2007-2014 by the Sphinx team, see AUTHORS.
 * :license: BSD, see LICENSE for details.
 *
 */


/**
 * Search Module
 */
var Search = {

  _index : null,
  _modules : null,
  _queued_query : null,
  _active_query : null,

  loadIndex : function(url) {
    $.ajax({type: "GET", url: url, data: null,
            dataType: "script", cache: true,
            complete: function(jqxhr, textstatus) {
              if (textstatus != "success") {
                document.getElementById("searchindexloader").src = url;
              }
            }});
  },

  setIndex : function(index) {
    var q;
    this._index = index;
    this._modules = Search.getModules();
    if ((q = this._queued_query) !== null) {
      this._queued_query = null;
      Search.query(q);
    }
  },

  hasIndex : function() {
      return this._index !== null;
  },

  deferQuery : function(query) {
      this._queued_query = query;
  },

  /**
   * perform a search for something (or wait until index is loaded)
   */
  performSearch : function(query) {
    // set new query to stop active ones
    if (query == Search._active_query)
        return;
    Search._active_query = query;
    this.output = $('#search-results');

    if (this.hasIndex())
      this.query(query);
    else
      this.deferQuery(query);
  },

  getModules : function() {
    var results = [];
    var modules = this._index.modules;

    for(var i in modules) {
        var name = modules[i];
        results.push([name + "/index", name, "", 0]);
    }

    return results;
  },

  /**
   * execute search (requires search index to be loaded)
   */
  query : function(query) {
    var parts = query.split(/\s+/);
    // filter out empty ones
    parts = parts.filter(function(e){return e}); 

    var max_entries = 300;
    var show_first = 20;
    var results = [];

    if(!parts.length) {
        results = this._modules.slice(0);
        // XXX: show all entries
        max_entries = 99999;
        show_first = max_entries;
    } else {
        // array of [filename, title, anchor, score]
        results = this.getResult(parts);
    }

    // now sort the results by score (in opposite order of appearance, since the
    // display function below uses pop() to retrieve items) and then
    // alphabetically
    results.sort(function(a, b) {
      var left = a[3];
      var right = b[3];
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

    if (results.length > max_entries)
        results = results.slice(results.length - max_entries, results.length);

    function displayNextItem(query, entry_index) {
      if (query !== Search._active_query || !results.length)
        return;

      var item = results.pop();
      var listItem = $('<li style="display:none"></li>');
      listItem.append($('<a/>').attr('href',
        item[0] + ".html" +
        item[2]).attr('target', 'Content').html(item[1]));
      Search.output.append(listItem);

      // show the first 30 immediately, then delay updates
      if (entry_index < show_first) {
        listItem.show();
        displayNextItem(query, entry_index + 1);
      } else {
        listItem.slideDown(5, function() {
          displayNextItem(query, entry_index + 1);
        });
      }
    }

    $('#search-results').empty();
    displayNextItem(query, 1);
  },

  /**
   * search for object names
   */
  getResult : function(parts) {
    var filenames = this._index.filenames;
    var objects = this._index.objects;
    var objnames = this._index.objnames;
    var titles = this._index.titles;

    var results = [];

    if(!parts.length) {
        return []
        h = new Object();

        var filenamesLength = filenames.length;
        for(var i=0; i < filenamesLength; i++) {
            var fn = filenames[i];
            var name = fn.split("/")[0].replace("-", " ")
            h[name] = fn;
        }

        for(var name in h) {
            var path = h[name].split("/")[0] + "/index";
            results.push([path, name, '#', 1]);
        }

        return results;
    }

    var do_score = function (text, part) {
        // returns -1 if not found, or a score >= 0

        var lower_text = text.toLowerCase();
        var lower_part = part.toLowerCase();

        // it's not in there
        if(lower_text.indexOf(lower_part) == -1)
            return -1;

        // prefer more matching text
        var lower_count = lower_text.split(lower_part).length - 1;
        score = (lower_count * part.length) / text.length;

        // prefer when it starts a part (either beginning or afer a ".")
        if(("." + lower_text).indexOf("." + lower_part) != -1)
            score *= 2;

        return score;
    };

    var partsLength = parts.length;
    var titleLength = titles.length;
    for (var i = 0; i < titleLength; i++) {
        var title = titles[i];
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
            // titles get shown last, thus -100
            results.push([
                filenames[i], title + " <small>(page)</small>",
                '', all_score - 100]);
        }
    }

    for (var prefix in objects) {
      for (var name in objects[prefix]) {
        var fullname = (prefix ? prefix + '.' : '') + name;
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
            var anchor = match[3];
            if (anchor === '')
                anchor = fullname;
            else if (anchor == '-')
                anchor = objnames[match[1]][1] + '-' + fullname;
            var type_name = objnames[match[1]][1]
            var filename = filenames[match[0]];

            // prefix properties and signals
            var is_sig_prop = false;
            if(type_name == "property") {
                fullname = ":" + fullname;
                is_sig_prop = true;
            } else if(type_name == "signal") {
                fullname = "::" + fullname;
                is_sig_prop = true
            }

            // Move the type name to the front
            if(is_sig_prop) {
                var start = fullname.indexOf("(");
                var cls = fullname.slice(start + 1, fullname.length - 1);
                fullname = cls + fullname.slice(0, start);
            }

            results.push([
                filename,
                fullname + " <small>(" + type_name + ")</small>",
                '#' + anchor, all_score]);
        }
      }
    }

    return results;
  }
};
