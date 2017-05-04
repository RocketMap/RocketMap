/* Main stats page */
var rawDataIsLoading = false
var statusPagePassword = false
var groupByWorker = true
var showHashTable = true
var showWorkersTable = true
var hashkeys = {}

// Raw data updating
var minUpdateDelay = 1000 // Minimum delay between updates (in ms).
var lastRawUpdateTime = new Date()

function getFormattedDate(unFormattedDate) { // eslintrc no-undef.
    // Use YYYY-MM-DD HH:MM:SS formatted dates to enable simple sorting.
    return moment(unFormattedDate).format('YYYY-MM-DD HH:mm:ss')
}

/*
 * Workers
 */
function addMainWorker(hash) {
    var worker = `
     <div id="worker_${hash}" class="worker">
       <span id="name_${hash}" class="name"></span>
       <span id="method_${hash}" class="method"></span>
       <span id="message_${hash}" class="message"></span>
     </div>
   `

    $(worker).appendTo('#status_container')
    addTable(hash)
}

function processMainWorker(i, worker) {
    var hash = hashFnv32a(worker['worker_name'], true)

    if ($('#worker_' + hash).length === 0) {
        addMainWorker(hash)
    }


    $('#name_' + hash).html(worker['worker_name'])
    $('#method_' + hash).html('(' + worker['method'] + ')')
    $('#message_' + hash).html(worker['message'].replace(/\n/g, '<br>'))
}

function addWorker(mainWorkerHash, workerHash) {
    var row = `
     <div id="row_${workerHash}" class="status_row">
       <div id="username_${workerHash}" class="status_cell"/>
       <div id="success_${workerHash}"  class="status_cell"/>
       <div id="fail_${workerHash}"     class="status_cell"/>
       <div id="no_items_${workerHash}"  class="status_cell"/>
       <div id="skip_${workerHash}"     class="status_cell"/>
       <div id="captchas_${workerHash}" class="status_cell"/>
       <div id="lastmod_${workerHash}"  class="status_cell"/>
       <div id="message_${workerHash}"  class="status_cell"/>
     </div>
   `
    $(row).appendTo('#table_' + mainWorkerHash)
}

function addHashtable(mainKeyHash, keyHash) {
    var hashrow = `
    <div id="hashrow_${keyHash}" class="status_row">
      <div id="key_${keyHash}" class="status_cell"/>
      <div id="maximum_${keyHash}" class="status_cell"/>
      <div id="remaining_${keyHash}" class="status_cell"/>
      <div id="usage_${keyHash}" class="status_cell"/>
      <div id="peak_${keyHash}" class="status_cell"/>
      <div id="expires_${keyHash}" class="status_cell"/>
      <div id="last_updated_${keyHash}" class="status_cell"/>
    </div>
    `
    $(hashrow).appendTo('#hashtable_' + mainKeyHash)
}

function processWorker(i, worker) {
    var hash = hashFnv32a(worker['username'], true)
    var mainWorkerHash
    if (groupByWorker) {
        mainWorkerHash = hashFnv32a(worker['worker_name'], true)
        if ($('#table_' + mainWorkerHash).length === 0) {
            return
        }
    } else {
        mainWorkerHash = 'global'
        if ($('#table_global').length === 0) {
            addTable('global')
        }
    }

    if ($('#row_' + hash).length === 0) {
        addWorker(mainWorkerHash, hash)
    }

    var lastModified = getFormattedDate(new Date(worker['last_modified']))

    $('#username_' + hash).html(worker['username'])
    $('#success_' + hash).html(worker['success'])
    $('#fail_' + hash).html(worker['fail'])
    $('#no_items_' + hash).html(worker['no_items'])
    $('#skip_' + hash).html(worker['skip'])
    $('#captchas_' + hash).html(worker['captcha'])
    $('#lastmod_' + hash).html(lastModified)
    $('#message_' + hash).html(worker['message'])
}

function processHashKeys(i, hashkey) {
    var key = hashkey['key']
    var keyHash = hashFnv32a(key, true)
    if ($('#hashtable_global').length === 0) {
        createHashTable('global')
    }

    if ($('#hashrow_' + keyHash).length === 0) {
        addHashtable('global', keyHash)
        var keyValues = {
            samples: [],
            nextSampleIndex: 0
        }

        hashkeys[key] = keyValues
    }

    // Calculate average value for Hash keys.
    var writeIndex = hashkeys[key].nextSampleIndex % 60
    hashkeys[key].nextSampleIndex += 1
    hashkeys[key].samples[writeIndex] = hashkey['maximum'] - hashkey['remaining']
    var numSamples = hashkeys[key].samples.length
    var sumSamples = 0
    for (var j = 0; j < numSamples; j++) {
        sumSamples += hashkeys[key].samples[j]
    }

    var usage = sumSamples / Math.max(numSamples, 1) // Avoid division by zero.

    var lastUpdated = getFormattedDate(new Date(hashkey['last_updated']))
    var expires = getFormattedDate(new Date(hashkey['expires']))
    if (!moment(expires).unix()) {
        expires = 'Unknown/Invalid'
    } else if (moment().isSameOrAfter(moment(expires))) {
        expires = 'Expired'
    }

    $('#key_' + keyHash).html(key)
    $('#maximum_' + keyHash).html(hashkey['maximum'])
    $('#remaining_' + keyHash).html(hashkey['remaining'])
    $('#usage_' + keyHash).html(usage.toFixed(2))
    $('#peak_' + keyHash).html(hashkey['peak'])
    $('#last_updated_' + keyHash).html(lastUpdated)
    $('#expires_' + keyHash).html(expires)
}

function parseResult(result) {
    if (groupByWorker && showWorkersTable) {
        $.each(result.main_workers, processMainWorker)
    }
    if (showWorkersTable) {
        $.each(result.workers, processWorker)
    }
    if (showHashTable) {
        $.each(result.hashkeys, processHashKeys)
    }
}
/*
 * Tables
 */
function createHashTable(mainKeyHash) {
    var hashtable = `
    <div class="status_table" id="hashtable_${mainKeyHash}">
     <div class="status_row header">
     <div class="status_cell">
       Hash Keys
      </div>
      <div class="status_cell">
        Maximum RPM
      </div>
      <div class="status_cell">
        RPM Left
      </div>
      <div class="status_cell">
        Usage
        </div>
      <div class="status_cell">
        Peak
        </div>
       <div class="status_cell">
         Expires At
       </div>
       <div class="status_cell">
         Last Modified
       </div>
     </div>
   </div>`

    hashtable = $(hashtable)
    $('#status_container').prepend(hashtable)
    $(hashtable).find('.status_row.header .status_cell').click(sortHashTable)
}

function sortHashTable() {
    var hashtable = $(this).parents('.status_table').first()
    var comparator = compareHashTable($(this).index())
    var hashrow = hashtable.find('.status_row:gt(0)').toArray()
    // Sort the array.
    hashrow.sort(comparator)
    this.asc = !this.asc
    if (!this.asc) {
        hashrow = hashrow.reverse()
    }
    for (var i = 0; i < hashrow.length; i++) {
        hashtable.append(hashrow[i])
    }
}

function getHashtableValue(hashrow, index) {
    return $(hashrow).children('.status_cell').eq(index).html()
}

function addTable(hash) {
    var table = `
     <div class="status_table" id="table_${hash}">
       <div class="status_row header">
         <div class="status_cell">
           Username
         </div>
         <div class="status_cell">
           Success
         </div>
         <div class="status_cell">
           Fail
         </div>
         <div class="status_cell">
           No Items
         </div>
         <div class="status_cell">
           Skipped
         </div>
         <div class="status_cell">
           Captchas
         </div>
         <div class="status_cell">
           Last Modified
         </div>
         <div class="status_cell">
           Message
         </div>
       </div>
     </div>`

    table = $(table)
    table.appendTo('#status_container')
    table.find('.status_row.header .status_cell').click(tableSort)
}

function tableSort() {
    var table = $(this).parents('.status_table').first()
    var comparator = compare($(this).index())
    var rows = table.find('.status_row:gt(0)').toArray()
    // Sort the array.
    rows.sort(comparator)
    this.asc = !this.asc
    if (!this.asc) {
        rows = rows.reverse()
    }
    for (var i = 0; i < rows.length; i++) {
        table.append(rows[i])
    }
}

function getCellValue(row, index) {
    return $(row).children('.status_cell').eq(index).html()
}

/*
 * Helpers
 */
function compare(index) {
    return function (a, b) {
        var valA = getCellValue(a, index)
        var valB = getCellValue(b, index)
        return $.isNumeric(valA) && $.isNumeric(valB) ? valA - valB : valA.localeCompare(valB)
    }
}

function compareHashTable(index) {
    return function (a, b) {
        var valA = getHashtableValue(a, index)
        var valB = getHashtableValue(b, index)
        return $.isNumeric(valA) && $.isNumeric(valB) ? valA - valB : valA.localeCompare(valB)
    }
}

function updateStatus() {
    lastRawUpdateTime = new Date()
    loadRawData().done(function (result) {
        // Parse result on success.
        parseResult(result)
    }).always(function () {
        // Only queue next request when previous is over.
        // Minimum delay of minUpdateDelay.
        var diff = new Date() - lastRawUpdateTime
        var delay = Math.max(minUpdateDelay - diff, 1) // Don't go below 1.

        // Don't use interval.
        window.setTimeout(updateStatus, delay)
    })
}

/**
 * Calculate a 32 bit FNV-1a hash
 * Found here: https://gist.github.com/vaiorabbit/5657561
 * Ref.: http://isthe.com/chongo/tech/comp/fnv/
 *
 * @param {string} str the input value
 * @param {boolean} [asString=false] set to true to return the hash value as
 *     8-digit hex string instead of an integer
 * @param {integer} [seed] optionally pass the hash of the previous chunk
 * @returns {integer | string}
 */
function hashFnv32a(str, asString, seed) {
    /* jshint bitwise:false */
    var i
    var l
    var hval = (seed === undefined) ? 0x811c9dc5 : seed

    for (i = 0, l = str.length; i < l; i++) {
        hval ^= str.charCodeAt(i)
        hval += (hval << 1) + (hval << 4) + (hval << 7) + (hval << 8) + (hval << 24)
    }

    if (asString) {
        // Convert to 8 digit hex string
        return ('0000000' + (hval >>> 0).toString(16)).substr(-8)
    }
    return hval >>> 0
}

function loadRawData() {
    return $.ajax({
        url: 'status',
        type: 'post',
        data: {
            'password': statusPagePassword
        },
        dataType: 'json',
        beforeSend: function () {
            if (rawDataIsLoading) {
                return false
            } else {
                rawDataIsLoading = true
            }
        },
        complete: function () {
            rawDataIsLoading = false
        }
    })
}


/*
 * Document ready
 */
$(document).ready(function () {
    // Set focus on password field.
    $('#password').focus()

    // Register to events.
    $('#password_form').submit(function (event) {
        event.preventDefault()

        statusPagePassword = $('#password').val()

        loadRawData().done(function (result) {
            if (result.login === 'ok') {
                $('.status_form').remove()
                parseResult(result)
                window.setTimeout(updateStatus, minUpdateDelay)
            } else {
                $('.status_form').effect('bounce')
                $('#password').focus()
            }
        })
    })

    $('#groupbyworker-switch').change(function () {
        groupByWorker = this.checked

        $('#status_container .status_table').remove()
        $('#status_container .worker').remove()
    })

    $('#hashkey-switch').change(function () {
        showHashTable = this.checked

        $('#status_container .status_table').remove()
        $('#status_container .worker').remove()
    })

    $('#showworker-switch').change(function () {
        showWorkersTable = this.checked

        $('#status_container .status_table').remove()
        $('#status_container .worker').remove()
    })
})
