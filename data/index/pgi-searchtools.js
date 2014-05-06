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

  /**
   * execute search (requires search index to be loaded)
   */
  query : function(query) {
    var parts = query.split(/\s+/);

    // array of [filename, title, anchor, score]
    var results = this.getResult(parts);

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

    var max_entries = 300;
    var show_first = 30;
    results = results.slice(results.length - max_entries, results.length);

    function displayNextItem(query, entry_index) {
      if (query !== Search._active_query || !results.length)
        return;

      var item = results.pop();
      var listItem = $('<li style="display:none"></li>');
      listItem.append($('<a/>').attr('href',
        item[0] + DOCUMENTATION_OPTIONS.FILE_SUFFIX +
        item[2]).attr('target', 'Content').html(item[1]));
      Search.output.append(listItem);

      // show the first 30 immediately, then delay updates
      var timeout = 5;
      if (entry_index < show_first)
        var timeout = 0;
      listItem.slideDown(timeout, function() {
        displayNextItem(query, entry_index + 1);
      });
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

    parts = parts.filter(function(e){return e}); 
    if(!parts.length)
        return [];

    var results = [];

    var do_score = function (text, part) {
        // returns -1 if not found, or a score >= 0

        var lower_text = text.toLowerCase();
        var lower_part = part.toLowerCase();
        var score = 0;

        // it's in there
        if(lower_text.indexOf(lower_part) < 0)
            return -1;

        // it's also in there without lower casing
        if(text.indexOf(part) != -1)
            score++;

        // it's at the beginning
        if(lower_text.indexOf(lower_part) == 0)
            score++;

        // it matches a part completely
        if (lower_text.length == lower_part.length)
            score++;
        else if(lower_text.indexOf("." + lower_part + ".") != -1)
            score++;
        else {
            var lastIndex = lower_text.length - (lower_part + 1);
            if(lower_text.indexOf(lower_part + ".") == 0)
                score++;
            else if(lower_text.indexOf("." + lower_part) == lastIndex)
                score++;
        }

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
            results.push([
                filenames[match[0]],
                fullname + " <small>(" + type_name + ")</small>",
                '#' + anchor, all_score]);
        }
      }
    }

    return results;
  }
};
