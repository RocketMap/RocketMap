/* Main stats page */
var rawDataIsLoading = false

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
        },
        error: function () {
            // Display error toast
            toastr['error']('Request failed while getting data. Retrying...', 'Error getting data')
            toastr.options = {
                'closeButton': true,
                'debug': false,
                'newestOnTop': true,
                'progressBar': false,
                'positionClass': 'toast-top-right',
                'preventDuplicates': true,
                'onclick': null,
                'showDuration': '300',
                'hideDuration': '1000',
                'timeOut': '25000',
                'extendedTimeOut': '1000',
                'showEasing': 'swing',
                'hideEasing': 'linear',
                'showMethod': 'fadeIn',
                'hideMethod': 'fadeOut'
            }
        }
    })
}

function processSeen(seen) {
    $('#stats_table > tbody').empty()

    for (var i = 0; i < seen.pokemon.length; i++) {
        var pokemonItem = seen.pokemon[i]
        var seenPercent = (pokemonItem.count / seen.total) * 100

        $('#stats_table > tbody')
            .append(`<tr class="status_row">
                        <td class="status_cell">
                            <i class="pokemon-sprite n${pokemonItem.pokemon_id}"</i>
                        </td>
                        <td class="status_cell">
                            ${pokemonItem.pokemon_id}                        
                        </td>
                        <td class="status_cell">
                            <a href="http://pokemon.gameinfo.io/en/pokemon/${pokemonItem.pokemon_id}" target="_blank" title="View in Pokedex">
                                ${pokemonItem.pokemon_name}
                            </a>
                        </td>
                        <td class="status_cell" data-sort="${pokemonItem.count}">
                            ${pokemonItem.count.toLocaleString()}
                        </td>
                        <td class="status_cell" data-sort="${seenPercent}">
                            ${seenPercent.toLocaleString(undefined, {minimumFractionDigits: 4, maximumFractionDigits: 4})}
                        </td>
                        <td class="status_cell">
                            ${moment(pokemonItem.disappear_time).format('H:mm:ss D MMM YYYY')}
                        </td>
                        <td class="status_cell">
                            ${pokemonItem.latitude.toFixed(7)}, ${pokemonItem.longitude.toFixed(7)}
                        </td>
                        <td class="status_cell">
                            <a href="javascript:void(0);" onclick="javascript:showOverlay(${pokemonItem.pokemon_id});">
                                All Locations
                            </a>
                        </td>
                     </tr>`)
    }
}

function updateStats() {
    $('#status_container').hide()
    $('#loading').show()

    loadRawData().done(function (result) {
        $('#stats_table')
                .DataTable()
                .destroy()

        $('#status_container').show()
        $('#loading').hide()

        processSeen(result.seen)

        var header = 'Pokemon Seen in ' + $('#duration option:selected').text()
        $('#name').html(header)
        $('#message').html('Total: ' + result.seen.total.toLocaleString())
        $('#stats_table')
            .DataTable({
                paging: false,
                searching: false,
                info: false,
                order: [[3, 'desc']],
                'scrollY': '75vh',
                'stripeClasses': ['status_row'],
                'columnDefs': [
                    {'orderable': false, 'targets': [0, 7]}
                ]
            })
    }).fail(function () {
        // Wait for next retry.
        setTimeout(updateStats, 1000)
    })
}

$('#duration')
    .select2({
        minimumResultsForSearch: Infinity
    })
    .on('change', updateStats)

updateStats()

/* Overlay */
var detailsLoading = false
var appearancesTimesLoading = false
var pokemonid = 0
var mapLoaded = false
var detailsPersist = false
var map = null
var heatmap = null
var heatmapPoints = []
var msPerMinute = 60000
var spawnTimeMinutes = 15
var spawnTimeMs = msPerMinute * spawnTimeMinutes
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
        },
        error: function () {
            // Display error toast
            toastr['error']('Request failed while getting data. Retrying...', 'Error getting data')
            toastr.options = {
                'closeButton': true,
                'debug': false,
                'newestOnTop': true,
                'progressBar': false,
                'positionClass': 'toast-top-right',
                'preventDuplicates': true,
                'onclick': null,
                'showDuration': '300',
                'hideDuration': '1000',
                'timeOut': '25000',
                'extendedTimeOut': '1000',
                'showEasing': 'swing',
                'hideEasing': 'linear',
                'showMethod': 'fadeIn',
                'hideMethod': 'fadeOut'
            }
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
        const isBounceDisabled = true // We don't need this functionality in our heatmap..
        const scaleByRarity = false   // ..nor this..
        const isNotifyPkmn = false    // ..and especially not this.

        if (item['marker']) {
            item['marker'].setMap(null)
        }
        item['marker'] = setupPokemonMarker(item, map, isBounceDisabled, scaleByRarity, isNotifyPkmn)
        item['marker'].setMap(map)
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
            const isBounceDisabled = true // We don't need this functionality in our heatmap..
            const scaleByRarity = false   // ..nor this..
            const isNotifyPkmn = false    // ..and especially not this.

            item['marker'].setMap(null)
            const newMarker = setupPokemonMarker(item, map, isBounceDisabled, scaleByRarity, isNotifyPkmn)
            newMarker.setMap(map)
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
            saw = moment(saw).format('H:mm:ss D MMM YYYY')

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
    }).fail(function () {
        // Wait for next retry.
        setTimeout(updateDetails, 1000)
    })
}

if (location.href.match(/overlay_[0-9]+/g)) {
    showOverlay(location.href.replace(/^.*overlay_([0-9]+).*$/, '$1'))
}
