/* Shared */
var monthArray = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


/* Main stats page */
var rawDataIsLoading = false
var statusPagePassword = false
var groupByWorker = true

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
function hashFnv32a (str, asString, seed) {
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

function loadRawData () {
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

function addTable (hash) {
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
          Last Modified
        </div>
        <div class="status_cell">
          Message
        </div>
      </div>
    </div>
  `

  table = $(table)
  table.appendTo('#status_container')
  table.find('.status_row.header .status_cell').click(tableSort)
}

function addMainWorker (hash) {
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

function processMainWorker (i, worker) {
  var hash = hashFnv32a(worker['worker_name'], true)

  if ($('#worker_' + hash).length === 0) {
    addMainWorker(hash)
  }

  $('#name_' + hash).html(worker['worker_name'])
  $('#method_' + hash).html('(' + worker['method'] + ')')
  $('#message_' + hash).html(worker['message'])
}

function addWorker (mainWorkerHash, workerHash) {
  var row = `
    <div id="row_${workerHash}" class="status_row">
      <div id="username_${workerHash}" class="status_cell"/>
      <div id="success_${workerHash}"  class="status_cell"/>
      <div id="fail_${workerHash}"     class="status_cell"/>
      <div id="no_items_${workerHash}"  class="status_cell"/>
      <div id="skip_${workerHash}"     class="status_cell"/>
      <div id="lastmod_${workerHash}"  class="status_cell"/>
      <div id="message_${workerHash}"  class="status_cell"/>
    </div>
  `

  $(row).appendTo('#table_' + mainWorkerHash)
}

function processWorker (i, worker) {
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

  var lastModified = new Date(worker['last_modified'])
  lastModified = lastModified.getHours() + ':' +
    ('0' + lastModified.getMinutes()).slice(-2) + ':' +
    ('0' + lastModified.getSeconds()).slice(-2) + ' ' +
    lastModified.getDate() + ' ' +
    monthArray[lastModified.getMonth()] + ' ' +
    lastModified.getFullYear()

  $('#username_' + hash).html(worker['username'])
  $('#success_' + hash).html(worker['success'])
  $('#fail_' + hash).html(worker['fail'])
  $('#no_items_' + hash).html(worker['no_items'])
  $('#skip_' + hash).html(worker['skip'])
  $('#lastmod_' + hash).html(lastModified)
  $('#message_' + hash).html(worker['message'])
}

function parseResult (result) {
  if (groupByWorker) {
    $.each(result.main_workers, processMainWorker)
  }
  $.each(result.workers, processWorker)
}

function updateStatus (firstRun) {
  loadRawData().done(function (result) {
    parseResult(result)
  })
}

$('#password_form').submit(function (event) {
  event.preventDefault()
  statusPagePassword = $('#password').val()
  loadRawData().done(function (result) {
    if (result.login === 'ok') {
      $('.status_form').remove()
      window.setInterval(updateStatus, 5000)
      parseResult(result)
    } else {
      $('.status_form').effect('bounce')
    }
  })
})

$('#groupbyworker-switch').change(function () {
  groupByWorker = this.checked
  $('#status_container .status_table').remove()
  $('#status_container .worker').remove()
  if (statusPagePassword) {
    updateStatus()
  }
})

function tableSort () {
  var table = $(this).parents('.status_table').eq(0)
  var rows = table.find('.status_row:gt(0)').toArray().sort(compare($(this).index()))
  this.asc = !this.asc
  if (!this.asc) {
    rows = rows.reverse()
  }
  for (var i = 0; i < rows.length; i++) {
    table.append(rows[i])
  }
}

function compare (index) {
  return function (a, b) {
    var valA = getCellValue(a, index)
    var valB = getCellValue(b, index)
    return $.isNumeric(valA) && $.isNumeric(valB) ? valA - valB : valA.localeCompare(valB)
  }
}

function getCellValue (row, index) {
  return $(row).children('.status_cell').eq(index).html()
}
