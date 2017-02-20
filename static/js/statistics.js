/* Shared */
var monthArray = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

/* Main stats page */
var rawDataIsLoading = false
var totalPokemon = 493
var msPerMinute = 60000
var spawnTimeMinutes = 15
var spawnTimeMs = msPerMinute * spawnTimeMinutes

function loadRawData() {
    return $.ajax({
        url: 'raw_data',
        type: 'GET',
        data: {
            'pokemon': false,
            'pokestops': false,
            'gyms': false,
            'scanned': false,
            'seen': true,
            'duration': $('#duration').val()
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

function addElement(pokemonId, name) {
    jQuery('<div/>', {
        id: 'seen_' + pokemonId,
        class: 'item'
    }).appendTo('#seen_container')

    jQuery('<div/>', {
        id: 'seen_' + pokemonId + '_base',
        class: 'container'
    }).appendTo('#seen_' + pokemonId)

    var imageContainer = jQuery('<div/>', {
        class: 'image'
    }).appendTo('#seen_' + pokemonId + '_base')

    jQuery('<i/>', {
        class: 'pokemon-sprite n' + pokemonId
    }).appendTo(imageContainer)

    var baseDetailContainer = jQuery('<div/>', {
        class: 'info'
    }).appendTo('#seen_' + pokemonId + '_base')

    jQuery('<div/>', {
        id: 'name_' + pokemonId,
        class: 'name'
    }).appendTo(baseDetailContainer)

    jQuery('<a/>', {
        id: 'link_' + pokemonId,
        href: 'http://www.pokemon.com/us/pokedex/' + pokemonId,
        target: '_blank',
        title: 'View in Pokedex',
        text: name
    }).appendTo('#name_' + pokemonId)

    jQuery('<div/>', {
        id: 'seen_' + pokemonId + '_details',
        class: 'details'
    }).appendTo('#seen_' + pokemonId)

    jQuery('<div/>', {
        id: 'count_' + pokemonId,
        class: 'seen'
    }).appendTo('#seen_' + pokemonId + '_details')

    jQuery('<div/>', {
        id: 'lastseen_' + pokemonId,
        class: 'lastseen'
    }).appendTo('#seen_' + pokemonId + '_details')

    jQuery('<div/>', {
        id: 'location_' + pokemonId,
        class: 'location'
    }).appendTo('#seen_' + pokemonId + '_details')

    jQuery('<a/>', {
        href: 'javascript:void(0);',
        onclick: 'javascript:showOverlay(' + pokemonId + ');',
        text: 'All Locations'
    }).appendTo('#seen_' + pokemonId + '_details')
}

function processSeen(seen) {
    var i
    var total = seen.total
    var shown = []

    seen.pokemon.sort(function (a, b) {
        var sort = document.getElementById('sort')
        var order = document.getElementById('order')

        if (order.options[order.selectedIndex].value === 'desc') {
            var tmp = b
            b = a
            a = tmp
        }

        if (sort.options[sort.selectedIndex].value === 'id') {
            return a['pokemon_id'] - b['pokemon_id']
        } else if (sort.options[sort.selectedIndex].value === 'name') {
            if (a['pokemon_name'].toLowerCase() < b['pokemon_name'].toLowerCase()) {
                return -1
            }
            if (a['pokemon_name'].toLowerCase() > b['pokemon_name'].toLowerCase()) {
                return 1
            }
            return 0
        } else {
            // Default to count
            if (a['count'] === b['count']) { // Same count: order by id
                return b['pokemon_id'] - a['pokemon_id']
            }
            return a['count'] - b['count']
        }
    })

    for (i = seen.pokemon.length - 1; i >= 0; i--) {
        var item = seen.pokemon[i]
        var percentage = (item['count'] / total * 100).toFixed(4)
        var lastSeen = new Date(item['disappear_time'])
        lastSeen = lastSeen.getHours() + ':' +
        ('0' + lastSeen.getMinutes()).slice(-2) + ':' +
        ('0' + lastSeen.getSeconds()).slice(-2) + ' ' +
        lastSeen.getDate() + ' ' +
        monthArray[lastSeen.getMonth()] + ' ' +
        lastSeen.getFullYear()
        var location = (item['latitude'] * 1).toFixed(7) + ', ' + (item['longitude'] * 1).toFixed(7)
        if (!$('#seen_' + item['pokemon_id']).length) {
            addElement(item['pokemon_id'], item['pokemon_name'])
        }
        $('#count_' + item['pokemon_id']).html('<strong>Seen:</strong> ' + item['count'].toLocaleString() + ' (' + percentage + '%)')
        $('#lastseen_' + item['pokemon_id']).html('<strong>Last Seen:</strong> ' + lastSeen)
        $('#location_' + item['pokemon_id']).html('<strong>Location:</strong> ' + location)
        $('#seen_' + item['pokemon_id']).show()
        // Reverting to classic javascript here as it's supposed to increase performance
        document.getElementById('seen_container').insertBefore(document.getElementById('seen_' + item['pokemon_id']), document.getElementById('seen_container').childNodes[0])
        shown.push(item['pokemon_id'])
    }

    // Hide any unneeded items
    for (i = 1; i <= totalPokemon; i++) {
        if (shown.indexOf(i) < 0) {
            $('#seen_' + i).hide()
        }
    }

    document.getElementById('seen_total').innerHTML = 'Total: ' + total.toLocaleString()
}

function updateStatMap(firstRun) {
    var duration = document.getElementById('duration')
    var header = 'Pokemon Seen in ' + duration.options[duration.selectedIndex].text
    if ($('#seen_header').html() !== header) {
        $('#seen_container').hide()
        $('#loading').show()
        $('#seen_header').html('')
        $('#seen_total').html('')
    }
    loadRawData().done(function (result) {
        processSeen(result.seen)
        if ($('#seen_header').html() !== header) {
            $('#seen_header').html(header)
            $('#loading').hide()
            $('#seen_container').show()
        }
    })
}

updateStatMap()

/* Overlay */
var detailsLoading = false
var appearancesTimesLoading = false
var pokemonid = 0
var mapLoaded = false
var detailsPersist = false
var map = null
var heatmap = null
var heatmapPoints = []
mapData.appearances = {}

function loadDetails() {
    return $.ajax({
        url: 'raw_data',
        type: 'GET',
        data: {
            'pokemon': false,
            'pokestops': false,
            'gyms': false,
            'scanned': false,
            'appearances': true,
            'pokemonid': pokemonid,
            'duration': $('#duration').val()
        },
        dataType: 'json',
        beforeSend: function () {
            if (detailsLoading) {
                return false
            } else {
                detailsLoading = true
            }
        },
        complete: function () {
            detailsLoading = false
        }
    })
}

function loadAppearancesTimes(pokemonId, spawnpointId) {
    return $.ajax({
        url: 'raw_data',
        type: 'GET',
        data: {
            'pokemon': false,
            'pokestops': false,
            'gyms': false,
            'scanned': false,
            'appearances': false,
            'appearancesDetails': true,
            'pokemonid': pokemonId,
            'spawnpoint_id': spawnpointId,
            'duration': $('#duration').val()
        },
        dataType: 'json',
        beforeSend: function () {
            if (appearancesTimesLoading) {
                return false
            } else {
                appearancesTimesLoading = true
            }
        },
        complete: function () {
            appearancesTimesLoading = false
        }
    })
}

function showTimes(marker) {
    appearanceTab(mapData.appearances[marker.spawnpointId]).then(function (value) {
        $('#times_list').html(value)
        $('#times_list').show()
    })
}

function closeTimes() {
    $('#times_list').hide()
    detailsPersist = false
}

function addListeners(marker) { // eslint-disable-line no-unused-vars
    marker.addListener('click', function () {
        showTimes(marker)
        detailsPersist = true
    })

    marker.addListener('mouseover', function () {
        showTimes(marker)
    })

    marker.addListener('mouseout', function () {
        if (!detailsPersist) {
            $('#times_list').hide()
        }
    })

    return marker
}

// Override map.js initMap
function initMap() {
    map = new google.maps.Map(document.getElementById('location_map'), {
        zoom: 16,
        center: {
            lat: centerLat,
            lng: centerLng
        },
        fullscreenControl: false,
        streetViewControl: false,
        mapTypeControl: true,
        clickableIcons: false,
        mapTypeControlOptions: {
            style: google.maps.MapTypeControlStyle.DROPDOWN_MENU,
            position: google.maps.ControlPosition.RIGHT_TOP,
            mapTypeIds: [
                google.maps.MapTypeId.ROADMAP,
                google.maps.MapTypeId.SATELLITE,
                google.maps.MapTypeId.HYBRID,
                'nolabels_style',
                'dark_style',
                'style_light2',
                'style_pgo',
                'dark_style_nl',
                'style_light2_nl',
                'style_pgo_nl',
                'style_pgo_day',
                'style_pgo_night',
                'style_pgo_dynamic'
            ]
        }
    })

    var styleNoLabels = new google.maps.StyledMapType(noLabelsStyle, {
        name: 'No Labels'
    })
    map.mapTypes.set('nolabels_style', styleNoLabels)

    var styleDark = new google.maps.StyledMapType(darkStyle, {
        name: 'Dark'
    })
    map.mapTypes.set('dark_style', styleDark)

    var styleLight2 = new google.maps.StyledMapType(light2Style, {
        name: 'Light2'
    })
    map.mapTypes.set('style_light2', styleLight2)

    var stylePgo = new google.maps.StyledMapType(pGoStyle, {
        name: 'RocketMap'
    })
    map.mapTypes.set('style_pgo', stylePgo)

    var styleDarkNl = new google.maps.StyledMapType(darkStyleNoLabels, {
        name: 'Dark (No Labels)'
    })
    map.mapTypes.set('dark_style_nl', styleDarkNl)

    var styleLight2Nl = new google.maps.StyledMapType(light2StyleNoLabels, {
        name: 'Light2 (No Labels)'
    })
    map.mapTypes.set('style_light2_nl', styleLight2Nl)

    var stylePgoNl = new google.maps.StyledMapType(pGoStyleNoLabels, {
        name: 'RocketMap (No Labels)'
    })
    map.mapTypes.set('style_pgo_nl', stylePgoNl)

    var stylePgoDay = new google.maps.StyledMapType(pGoStyleDay, {
        name: 'RocketMap Day'
    })
    map.mapTypes.set('style_pgo_day', stylePgoDay)

    var stylePgoNight = new google.maps.StyledMapType(pGoStyleNight, {
        name: 'RocketMap Night'
    })
    map.mapTypes.set('style_pgo_night', stylePgoNight)

    // dynamic map style chooses stylePgoDay or stylePgoNight depending on client time
    var currentDate = new Date()
    var currentHour = currentDate.getHours()
    var stylePgoDynamic = (currentHour >= 6 && currentHour < 19) ? stylePgoDay : stylePgoNight
    map.mapTypes.set('style_pgo_dynamic', stylePgoDynamic)

    map.addListener('maptypeid_changed', function (s) {
        Store.set('map_style', this.mapTypeId)
    })

    map.setMapTypeId(Store.get('map_style'))
    google.maps.event.addListener(map, 'idle', updateStatMap)

    mapLoaded = true

    google.maps.event.addListener(map, 'zoom_changed', function () {
        redrawAppearances(mapData.appearances)
    })
}

function resetMap() {
    $.each(mapData.appearances, function (key, value) {
        mapData.appearances[key].marker.setMap(null)
        delete mapData.appearances[key]
    })

    heatmapPoints = []
    if (heatmap) {
        heatmap.setMap(null)
    }
}

function showOverlay(id) {
    // Only load google maps once, and only if requested
    if (!mapLoaded) {
        initMap()
    }
    resetMap()
    pokemonid = id
    $('#location_details').show()
    location.hash = 'overlay_' + pokemonid
    updateDetails()

    return false
}

function closeOverlay() { // eslint-disable-line no-unused-vars
    $('#location_details').hide()
    closeTimes()
    location.hash = ''
    return false
}

function processAppearance(i, item) {
    var spawnpointId = item['spawnpoint_id']
    if (!((spawnpointId) in mapData.appearances)) {
        if (item['marker']) {
            item['marker'].setMap(null)
        }
        item['marker'] = setupPokemonMarker(item, map, true)
        addListeners(item['marker'])
        item['marker'].spawnpointId = spawnpointId
        mapData.appearances[spawnpointId] = item
    }
    heatmapPoints.push({location: new google.maps.LatLng(item['latitude'], item['longitude']), weight: parseFloat(item['count'])})
}

function redrawAppearances(appearances) {
    $.each(appearances, function (key, value) {
        var item = appearances[key]
        if (!item['hidden']) {
            var newMarker = setupPokemonMarker(item, map, true)
            item['marker'].setMap(null)
            addListeners(newMarker)
            newMarker.spawnpointId = item['spawnpoint_id']
            appearances[key].marker = newMarker
        }
    })
}

function appearanceTab(item) {
    var times = ''
    return loadAppearancesTimes(item['pokemon_id'], item['spawnpoint_id']).then(function (result) {
        $.each(result.appearancesTimes, function (key, value) {
            var saw = new Date(value - spawnTimeMs)
            saw = saw.getHours() + ':' +
                    ('0' + saw.getMinutes()).slice(-2) + ':' +
                    ('0' + saw.getSeconds()).slice(-2) + ' ' +
                    saw.getDate() + ' ' +
                    monthArray[saw.getMonth()] + ' ' +
                    saw.getFullYear()
            times = '<div class="row' + (key % 2) + '">' + saw + '</div>' + times
        })
        return `<div>
                                <a href="javascript:closeTimes();">Close this tab</a>
                        </div>
                        <div class="row1">
                                <strong>Lat:</strong> ${item['latitude'].toFixed(7)}
                        </div>
                        <div class="row0">
                                <strong>Long:</strong> ${item['longitude'].toFixed(7)}
                        </div>
                        <div class="row1">
                            <strong>Appearances:</strong> ${item['count'].toLocaleString()}
                        </div>
                        <div class="row0"><strong>Times:</strong></div>
                        <div>
                                ${times}
                        </div>`
    })
}

function updateDetails() {
    loadDetails().done(function (result) {
        $.each(result.appearances, processAppearance)
        if (heatmap) {
            heatmap.setMap(null)
        }
        heatmap = new google.maps.visualization.HeatmapLayer({
            data: heatmapPoints,
            map: map,
            radius: 50
        })
    })
}

if (location.href.match(/overlay_[0-9]+/g)) {
    showOverlay(location.href.replace(/^.*overlay_([0-9]+).*$/, '$1'))
}

$('#nav select')
    .select2({
        minimumResultsForSearch: Infinity
    })
    .on('change', updateStatMap)
