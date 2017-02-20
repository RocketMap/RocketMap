//
// Global map.js variables
//

var $selectExclude
var $selectPokemonNotify
var $selectRarityNotify
var $textPerfectionNotify
var $selectStyle
var $selectIconSize
var $selectOpenGymsOnly
var $selectTeamGymsOnly
var $selectLastUpdateGymsOnly
var $selectMinGymLevel
var $selectMaxGymLevel
var $selectLuredPokestopsOnly
var $selectSearchIconMarker
var $selectGymMarkerStyle
var $selectLocationIconMarker
var $switchGymSidebar
var $timeoutDialog

var language = document.documentElement.lang === '' ? 'en' : document.documentElement.lang
var idToPokemon = {}
var i8lnDictionary = {}
var languageLookups = 0
var languageLookupThreshold = 3

var searchMarkerStyles

var timestamp
var excludedPokemon = []
var notifiedPokemon = []
var notifiedRarity = []
var notifiedMinPerfection = null

var buffer = []
var reincludedPokemon = []
var reids = []

var map
var rawDataIsLoading = false
var locationMarker
var rangeMarkers = ['pokemon', 'pokestop', 'gym']
var searchMarker
var storeZoom = true
var scanPath
var moves

var oSwLat
var oSwLng
var oNeLat
var oNeLng

var lastpokestops
var lastgyms
var lastpokemon
var lastslocs
var lastspawns

var selectedStyle = 'light'

var updateWorker
var lastUpdateTime

var gymTypes = ['Uncontested', 'Mystic', 'Valor', 'Instinct']
var gymPrestige = [2000, 4000, 8000, 12000, 16000, 20000, 30000, 40000, 50000]
var audio = new Audio('static/sounds/ding.mp3')

/*
  text place holders:
  <pkm> - pokemon name
  <prc> - iv in percent without percent symbol
  <atk> - attack as number
  <def> - defense as number
  <sta> - stamnia as number
*/
var notifyIvTitle = '<pkm> <prc>% (<atk>/<def>/<sta>)'
var notifyNoIvTitle = '<pkm>'

/*
  text place holders:
  <dist>  - disappear time
  <udist> - time until disappear
*/
var notifyText = 'disappears at <dist> (<udist>)'

//
// Functions
//

function excludePokemon(id) { // eslint-disable-line no-unused-vars
    $selectExclude.val(
        $selectExclude.val().concat(id)
    ).trigger('change')
}

function notifyAboutPokemon(id) { // eslint-disable-line no-unused-vars
    $selectPokemonNotify.val(
        $selectPokemonNotify.val().concat(id)
    ).trigger('change')
}

function removePokemonMarker(encounterId) { // eslint-disable-line no-unused-vars
    if (mapData.pokemons[encounterId].marker.rangeCircle) {
        mapData.pokemons[encounterId].marker.rangeCircle.setMap(null)
        delete mapData.pokemons[encounterId].marker.rangeCircle
    }
    mapData.pokemons[encounterId].marker.setMap(null)
    mapData.pokemons[encounterId].hidden = true
}

function initMap() { // eslint-disable-line no-unused-vars
    map = new google.maps.Map(document.getElementById('map'), {
        center: {
            lat: centerLat,
            lng: centerLng
        },
        zoom: Store.get('zoomLevel'),
        fullscreenControl: true,
        streetViewControl: false,
        mapTypeControl: false,
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
    map.addListener('idle', updateMap)

    map.addListener('zoom_changed', function () {
        if (storeZoom === true) {
            Store.set('zoomLevel', this.getZoom())
        } else {
            storeZoom = true
        }

        redrawPokemon(mapData.pokemons)
        redrawPokemon(mapData.lurePokemons)
    })

    searchMarker = createSearchMarker()
    locationMarker = createLocationMarker()
    createMyLocationButton()
    initSidebar()

    $('#scan-here').on('click', function () {
        var loc = map.getCenter()
        changeLocation(loc.lat(), loc.lng())

        if (!$('#search-switch').checked) {
            $('#search-switch').prop('checked', true)
            searchControl('on')
        }
    })
}

function updateLocationMarker(style) {
    if (style in searchMarkerStyles) {
        locationMarker.setIcon(searchMarkerStyles[style].icon)
        Store.set('locationMarkerStyle', style)
    }
    return locationMarker
}

function createLocationMarker() {
    var position = Store.get('followMyLocationPosition')
    var lat = ('lat' in position) ? position.lat : centerLat
    var lng = ('lng' in position) ? position.lng : centerLng

    var locationMarker = new google.maps.Marker({
        map: map,
        animation: google.maps.Animation.DROP,
        position: {
            lat: lat,
            lng: lng
        },
        draggable: true,
        icon: null,
        optimized: false,
        zIndex: google.maps.Marker.MAX_ZINDEX + 2
    })

    locationMarker.infoWindow = new google.maps.InfoWindow({
        content: '<div><b>My Location</b></div>',
        disableAutoPan: true
    })

    addListeners(locationMarker)

    google.maps.event.addListener(locationMarker, 'dragend', function () {
        var newLocation = locationMarker.getPosition()
        Store.set('followMyLocationPosition', {
            lat: newLocation.lat(),
            lng: newLocation.lng()
        })
    })

    return locationMarker
}

function updateSearchMarker(style) {
    if (style in searchMarkerStyles) {
        searchMarker.setIcon(searchMarkerStyles[style].icon)
        Store.set('searchMarkerStyle', style)
    }

    return searchMarker
}

function createSearchMarker() {
    var searchMarker = new google.maps.Marker({ // need to keep reference.
        position: {
            lat: centerLat,
            lng: centerLng
        },
        map: map,
        animation: google.maps.Animation.DROP,
        draggable: !Store.get('lockMarker'),
        icon: null,
        optimized: false,
        zIndex: google.maps.Marker.MAX_ZINDEX + 1
    })

    searchMarker.infoWindow = new google.maps.InfoWindow({
        content: '<div><b>Search Location</b></div>',
        disableAutoPan: true
    })

    addListeners(searchMarker)

    var oldLocation = null
    google.maps.event.addListener(searchMarker, 'dragstart', function () {
        oldLocation = searchMarker.getPosition()
    })

    google.maps.event.addListener(searchMarker, 'dragend', function () {
        var newLocation = searchMarker.getPosition()
        changeSearchLocation(newLocation.lat(), newLocation.lng())
            .done(function () {
                oldLocation = null
            })
            .fail(function () {
                if (oldLocation) {
                    searchMarker.setPosition(oldLocation)
                }
            })
    })

    return searchMarker
}

var searchControlURI = 'search_control'

function searchControl(action) {
    $.post(searchControlURI + '?action=' + encodeURIComponent(action))
    $('#scan-here').toggleClass('disabled', action === 'off')
}

function updateSearchStatus() {
    $.getJSON(searchControlURI).then(function (data) {
        $('#search-switch').prop('checked', data.status)
        $('#scan-here').toggleClass('disabled', !data.status)
    })
}

function initSidebar() {
    $('#gyms-switch').prop('checked', Store.get('showGyms'))
    $('#gym-sidebar-switch').prop('checked', Store.get('useGymSidebar'))
    $('#gym-sidebar-wrapper').toggle(Store.get('showGyms'))
    $('#gyms-filter-wrapper').toggle(Store.get('showGyms'))
    $('#team-gyms-only-switch').val(Store.get('showTeamGymsOnly'))
    $('#open-gyms-only-switch').val(Store.get('showOpenGymsOnly'))
    $('#min-level-gyms-filter-switch').val(Store.get('minGymLevel'))
    $('#max-level-gyms-filter-switch').val(Store.get('maxGymLevel'))
    $('#last-update-gyms-switch').val(Store.get('showLastUpdatedGymsOnly'))
    $('#pokemon-switch').prop('checked', Store.get('showPokemon'))
    $('#pokestops-switch').prop('checked', Store.get('showPokestops'))
    $('#lured-pokestops-only-switch').val(Store.get('showLuredPokestopsOnly'))
    $('#lured-pokestops-only-wrapper').toggle(Store.get('showPokestops'))
    $('#geoloc-switch').prop('checked', Store.get('geoLocate'))
    $('#lock-marker-switch').prop('checked', Store.get('lockMarker'))
    $('#start-at-user-location-switch').prop('checked', Store.get('startAtUserLocation'))
    $('#follow-my-location-switch').prop('checked', Store.get('followMyLocation'))
    $('#scan-here-switch').prop('checked', Store.get('scanHere'))
    $('#scan-here').toggle(Store.get('scanHere'))
    $('#scanned-switch').prop('checked', Store.get('showScanned'))
    $('#spawnpoints-switch').prop('checked', Store.get('showSpawnpoints'))
    $('#ranges-switch').prop('checked', Store.get('showRanges'))
    $('#sound-switch').prop('checked', Store.get('playSound'))
    var searchBox = new google.maps.places.Autocomplete(document.getElementById('next-location'))
    $('#next-location').css('background-color', $('#geoloc-switch').prop('checked') ? '#e0e0e0' : '#ffffff')

    updateSearchStatus()
    setInterval(updateSearchStatus, 5000)

    searchBox.addListener('place_changed', function () {
        var place = searchBox.getPlace()

        if (!place.geometry) return

        var loc = place.geometry.location
        changeLocation(loc.lat(), loc.lng())
    })

    $('#pokemon-icon-size').val(Store.get('iconSizeModifier'))
}

function pad(number) {
    return number <= 99 ? ('0' + number).slice(-2) : number
}

function getTypeSpan(type) {
    return `<span style='padding: 2px 5px; text-transform: uppercase; color: white; margin-right: 2px; border-radius: 4px; font-size: 0.8em; vertical-align: text-bottom; background-color: ${type['color']}'>${type['type']}</span>`
}

function openMapDirections(lat, lng) { // eslint-disable-line no-unused-vars
    var url = 'https://www.google.com/maps/?daddr=' + lat + ',' + lng
    window.open(url, '_blank')
}

function pokemonLabel(name, rarity, types, disappearTime, id, latitude, longitude, encounterId, atk, def, sta, move1, move2) {
    var disappearDate = new Date(disappearTime)
    var rarityDisplay = rarity ? '(' + rarity + ')' : ''
    var typesDisplay = ''
    var pMove1 = (moves[move1] !== undefined) ? i8ln(moves[move1]['name']) : 'gen/unknown'
    var pMove2 = (moves[move2] !== undefined) ? i8ln(moves[move2]['name']) : 'gen/unknown'

    $.each(types, function (index, type) {
        typesDisplay += getTypeSpan(type)
    })
    var details = ''
    if (atk != null) {
        var iv = getIv(atk, def, sta)
        details = `
            <div>
                IV: ${iv.toFixed(1)}% (${atk}/${def}/${sta})
            </div>
            <div>
                Moves: ${pMove1} / ${pMove2}
            </div>
            `
    }
    var contentstring = `
        <div>
            <b>${name}</b>
            <span> - </span>
            <small>
                <a href='http://www.pokemon.com/us/pokedex/${id}' target='_blank' title='View in Pokedex'>#${id}</a>
            </small>
            <span> ${rarityDisplay}</span>
            <span> - </span>
            <small>${typesDisplay}</small>
        </div>
        <div>
            Disappears at ${pad(disappearDate.getHours())}:${pad(disappearDate.getMinutes())}:${pad(disappearDate.getSeconds())}
            <span class='label-countdown' disappears-at='${disappearTime}'>(00m00s)</span>
        </div>
        <div>
            Location: ${latitude.toFixed(6)}, ${longitude.toFixed(7)}
        </div>
            ${details}
        <div>
            <a href='javascript:excludePokemon(${id})'>Exclude</a>&nbsp;&nbsp
            <a href='javascript:notifyAboutPokemon(${id})'>Notify</a>&nbsp;&nbsp
            <a href='javascript:removePokemonMarker("${encounterId}")'>Remove</a>&nbsp;&nbsp
            <a href='javascript:void(0);' onclick='javascript:openMapDirections(${latitude},${longitude});' title='View in Maps'>Get directions</a>
        </div>`
    return contentstring
}

function gymLabel(teamName, teamId, gymPoints, latitude, longitude, lastScanned = null, name = null, members = [], gymId) {
    var memberStr = ''
    for (var i = 0; i < members.length; i++) {
        memberStr += `
            <span class="gym-member" title="${members[i].pokemon_name} | ${members[i].trainer_name} (Lvl ${members[i].trainer_level})">
                <i class="pokemon-sprite n${members[i].pokemon_id}"></i>
                <span class="cp team-${teamId}">${members[i].pokemon_cp}</span>
            </span>`
    }

    var lastScannedStr
    if (lastScanned) {
        var lastScannedDate = new Date(lastScanned)
        lastScannedStr = `${lastScannedDate.getFullYear()}-${pad(lastScannedDate.getMonth() + 1)}-${pad(lastScannedDate.getDate())} ${pad(lastScannedDate.getHours())}:${pad(lastScannedDate.getMinutes())}:${pad(lastScannedDate.getSeconds())}`
    } else {
        lastScannedStr = 'Unknown'
    }
    var directionsStr = ''
    if (!Store.get('useGymSidebar')) {
        directionsStr = `<div>
                <a href='javascript:void(0);' onclick='javascript:openMapDirections(${latitude},${longitude});' title='View in Maps'>Get directions</a>
            </div>`
    }

    var nameStr = (name ? `<div>${name}</div>` : '')

    var gymColor = ['0, 0, 0, .4', '74, 138, 202, .6', '240, 68, 58, .6', '254, 217, 40, .6']
    var str
    if (teamId === 0) {
        str = `
            <div>
                <center>
                    <div>
                        <b style='color:rgba(${gymColor[teamId]})'>${teamName}</b><br>
                        <img height='70px' style='padding: 5px;' src='static/forts/${teamName}_large.png'>
                    </div>
                    ${nameStr}
                    <div>
                        Location: ${latitude.toFixed(6)}, ${longitude.toFixed(7)}
                    </div>
                    <div>
                        Last Scanned: ${lastScannedStr}
                    </div>
                    ${directionsStr}
                </center>
            </div>`
    } else {
        var gymLevel = getGymLevel(gymPoints)
        str = `
            <div>
                <center>
                    <div style='padding-bottom: 2px'>
                        Gym owned by:
                    </div>
                    <div>
                        <b style='color:rgba(${gymColor[teamId]})'>Team ${teamName}</b><br>
                        <img height='70px' style='padding: 5px;' src='static/forts/${teamName}_large.png'>
                    </div>
                    <div>
                        ${nameStr}
                    </div>
                    <div>
                        Level: ${gymLevel} | Prestige: ${gymPoints}/${gymPrestige[gymLevel - 1] || 50000}
                    </div>
                    <div>
                        ${memberStr}
                    </div>
                    <div>
                        Location: ${latitude.toFixed(6)}, ${longitude.toFixed(7)}
                    </div>
                    <div>
                        Last Scanned: ${lastScannedStr}
                    </div>
                    ${directionsStr}
                </center>
            </div>`
    }

    return str
}

function getGymLevel(points) {
    var level = 1
    while (points >= gymPrestige[level - 1]) {
        level++
    }

    return level
}

function pokestopLabel(expireTime, latitude, longitude) {
    var str
    if (expireTime) {
        var expireDate = new Date(expireTime)

        str = `
            <div>
                <b>Lured Pokéstop</b>
            </div>
            <div>
                Lure expires at ${pad(expireDate.getHours())}:${pad(expireDate.getMinutes())}:${pad(expireDate.getSeconds())}
                <span class='label-countdown' disappears-at='${expireTime}'>(00m00s)</span>
            </div>
            <div>
                Location: ${latitude.toFixed(6)}, ${longitude.toFixed(7)}
            </div>
            <div>
                <a href='javascript:void(0);' onclick='javascript:openMapDirections(${latitude},${longitude});' title='View in Maps'>Get directions</a>
            </div>`
    } else {
        str = `
            <div>
                <b>Pokéstop</b>
            </div>
            <div>
                Location: ${latitude.toFixed(6)}, ${longitude.toFixed(7)}
            </div>
            <div>
                <a href='javascript:void(0);' onclick='javascript:openMapDirections(${latitude},${longitude});' title='View in Maps'>Get directions</a>
            </div>`
    }

    return str
}

function formatSpawnTime(seconds) {
    // the addition and modulo are required here because the db stores when a spawn disappears
    // the subtraction to get the appearance time will knock seconds under 0 if the spawn happens in the previous hour
    return ('0' + Math.floor(((seconds + 3600) % 3600) / 60)).substr(-2) + ':' + ('0' + seconds % 60).substr(-2)
}

function spawnpointLabel(item) {
    var str = `
        <div>
            <b>Spawn Point</b>
        </div>
        <div>
            Every hour from ${formatSpawnTime(item.time)} to ${formatSpawnTime(item.time + 900)}
        </div>`

    if (item.special) {
        str += `
            <div>
                May appear as early as ${formatSpawnTime(item.time - 1800)}
            </div>`
    }
    return str
}

function addRangeCircle(marker, map, type, teamId) {
    var targetmap = null
    var circleCenter = new google.maps.LatLng(marker.position.lat(), marker.position.lng())
    var gymColors = ['#999999', '#0051CF', '#FF260E', '#FECC23'] // 'Uncontested', 'Mystic', 'Valor', 'Instinct']
    var teamColor = gymColors[0]
    if (teamId) teamColor = gymColors[teamId]

    var range
    var circleColor

    // handle each type of marker and be explicit about the range circle attributes
    switch (type) {
        case 'pokemon':
            circleColor = '#C233F2'
            range = 40 // pokemon appear at 40m and then you can move away. still have to be 40m close to see it though, so ignore the further disappear distance
            break
        case 'pokestop':
            circleColor = '#3EB0FF'
            range = 40
            break
        case 'gym':
            circleColor = teamColor
            range = 40
            break
    }

    if (map) targetmap = map

    var rangeCircleOpts = {
        map: targetmap,
        radius: range, // meters
        strokeWeight: 1,
        strokeColor: circleColor,
        strokeOpacity: 0.9,
        center: circleCenter,
        fillColor: circleColor,
        fillOpacity: 0.3
    }
    var rangeCircle = new google.maps.Circle(rangeCircleOpts)
    return rangeCircle
}

function isRangeActive(map) {
    if (map.getZoom() < 16) return false
    return Store.get('showRanges')
}

function getIv(atk, def, stm) {
    if (atk !== null) {
        return 100.0 * (atk + def + stm) / 45
    }

    return false
}

function lpad(str, len, padstr) {
    return Array(Math.max(len - String(str).length + 1, 0)).join(padstr) + str
}

function repArray(text, find, replace) {
    for (var i = 0; i < find.length; i++) {
        text = text.replace(find[i], replace[i])
    }

    return text
}

function getTimeUntil(time) {
    var now = +new Date()
    var tdiff = time - now

    var sec = Math.floor((tdiff / 1000) % 60)
    var min = Math.floor((tdiff / 1000 / 60) % 60)
    var hour = Math.floor((tdiff / (1000 * 60 * 60)) % 24)

    return {
        'total': tdiff,
        'hour': hour,
        'min': min,
        'sec': sec,
        'now': now,
        'ttime': time
    }
}

function getNotifyText(item) {
    var iv = getIv(item['individual_attack'], item['individual_defense'], item['individual_stamina'])
    var find = ['<prc>', '<pkm>', '<atk>', '<def>', '<sta>']
    var replace = [((iv) ? iv.toFixed(1) : ''), item['pokemon_name'], item['individual_attack'],
        item['individual_defense'], item['individual_stamina']]
    var ntitle = repArray(((iv) ? notifyIvTitle : notifyNoIvTitle), find, replace)
    var dist = (new Date(item['disappear_time'])).toLocaleString([], {
        hour: '2-digit', minute: '2-digit',
        second: '2-digit', hour12: false})
    var until = getTimeUntil(item['disappear_time'])
    var udist = (until.hour > 0) ? until.hour + ':' : ''
    udist += lpad(until.min, 2, 0) + 'm' + lpad(until.sec, 2, 0) + 's'
    find = ['<dist>', '<udist>']
    replace = [dist, udist]
    var ntext = repArray(notifyText, find, replace)

    return {
        'fav_title': ntitle,
        'fav_text': ntext
    }
}

function customizePokemonMarker(marker, item, skipNotification) {
    marker.addListener('click', function () {
        this.setAnimation(null)
        this.animationDisabled = true
    })

    if (!marker.rangeCircle && isRangeActive(map)) {
        marker.rangeCircle = addRangeCircle(marker, map, 'pokemon')
    }

    marker.infoWindow = new google.maps.InfoWindow({
        content: pokemonLabel(item['pokemon_name'], item['pokemon_rarity'], item['pokemon_types'], item['disappear_time'], item['pokemon_id'], item['latitude'], item['longitude'], item['encounter_id'], item['individual_attack'], item['individual_defense'], item['individual_stamina'], item['move_1'], item['move_2']),
        disableAutoPan: true
    })

    if (notifiedPokemon.indexOf(item['pokemon_id']) > -1 || notifiedRarity.indexOf(item['pokemon_rarity']) > -1) {
        if (!skipNotification) {
            if (Store.get('playSound')) {
                audio.play()
            }
            sendNotification(getNotifyText(item).fav_title, getNotifyText(item).fav_text, 'static/icons/' + item['pokemon_id'] + '.png', item['latitude'], item['longitude'])
        }
        if (marker.animationDisabled !== true) {
            marker.setAnimation(google.maps.Animation.BOUNCE)
        }
    }

    if (item['individual_attack'] != null) {
        var perfection = getIv(item['individual_attack'], item['individual_defense'], item['individual_stamina'])
        if (notifiedMinPerfection > 0 && perfection >= notifiedMinPerfection) {
            if (!skipNotification) {
                if (Store.get('playSound')) {
                    audio.play()
                }
                sendNotification(getNotifyText(item).fav_title, getNotifyText(item).fav_text, 'static/icons/' + item['pokemon_id'] + '.png', item['latitude'], item['longitude'])
            }
            if (marker.animationDisabled !== true) {
                marker.setAnimation(google.maps.Animation.BOUNCE)
            }
        }
    }

    addListeners(marker)
}

function setupGymMarker(item) {
    var marker = new google.maps.Marker({
        position: {
            lat: item['latitude'],
            lng: item['longitude']
        },
        map: map,
        icon: {
            url: 'static/forts/' + Store.get('gymMarkerStyle') + '/' + gymTypes[item['team_id']] + (item['team_id'] !== 0 ? '_' + getGymLevel(item['gym_points']) : '') + '.png',
            scaledSize: new google.maps.Size(48, 48)
        }
    })

    if (!marker.rangeCircle && isRangeActive(map)) {
        marker.rangeCircle = addRangeCircle(marker, map, 'gym', item['team_id'])
    }

    marker.infoWindow = new google.maps.InfoWindow({
        content: gymLabel(gymTypes[item['team_id']], item['team_id'], item['gym_points'], item['latitude'], item['longitude'], item['last_scanned'], item['name'], item['pokemon'], item['gym_id']),
        disableAutoPan: true
    })

    if (Store.get('useGymSidebar')) {
        marker.addListener('click', function () {
            var gymSidebar = document.querySelector('#gym-details')
            if (gymSidebar.getAttribute('data-id') === item['gym_id'] && gymSidebar.classList.contains('visible')) {
                gymSidebar.classList.remove('visible')
            } else {
                gymSidebar.setAttribute('data-id', item['gym_id'])
                showGymDetails(item['gym_id'])
            }
        })

        google.maps.event.addListener(marker.infoWindow, 'closeclick', function () {
            marker.persist = null
        })

        if (!isMobileDevice() && !isTouchDevice()) {
            marker.addListener('mouseover', function () {
                marker.infoWindow.open(map, marker)
                clearSelection()
                updateLabelDiffTime()
            })
        }

        marker.addListener('mouseout', function () {
            if (!marker.persist) {
                marker.infoWindow.close()
            }
        })
    } else {
        addListeners(marker)
    }
    return marker
}

function updateGymMarker(item, marker) {
    marker.setIcon({
        url: 'static/forts/' + Store.get('gymMarkerStyle') + '/' + gymTypes[item['team_id']] + (item['team_id'] !== 0 ? '_' + getGymLevel(item['gym_points']) : '') + '.png',
        scaledSize: new google.maps.Size(48, 48)
    })
    marker.infoWindow.setContent(gymLabel(gymTypes[item['team_id']], item['team_id'], item['gym_points'], item['latitude'], item['longitude'], item['last_scanned'], item['name'], item['pokemon'], item['gym_id']))
    return marker
}

function updateGymIcons() {
    $.each(mapData.gyms, function (key, value) {
        mapData.gyms[key]['marker'].setIcon({
            url: 'static/forts/' + Store.get('gymMarkerStyle') + '/' + gymTypes[mapData.gyms[key]['team_id']] + (mapData.gyms[key]['team_id'] !== 0 ? '_' + getGymLevel(mapData.gyms[key]['gym_points']) : '') + '.png',
            scaledSize: new google.maps.Size(48, 48)
        })
    })
}

function setupPokestopMarker(item) {
    var imagename = item['lure_expiration'] ? 'PstopLured' : 'Pstop'
    var marker = new google.maps.Marker({
        position: {
            lat: item['latitude'],
            lng: item['longitude']
        },
        map: map,
        zIndex: 2,
        icon: 'static/forts/' + imagename + '.png'
    })

    if (!marker.rangeCircle && isRangeActive(map)) {
        marker.rangeCircle = addRangeCircle(marker, map, 'pokestop')
    }

    marker.infoWindow = new google.maps.InfoWindow({
        content: pokestopLabel(item['lure_expiration'], item['latitude'], item['longitude']),
        disableAutoPan: true
    })

    addListeners(marker)
    return marker
}

function getColorByDate(value) {
    // Changes the color from red to green over 15 mins
    var diff = (Date.now() - value) / 1000 / 60 / 15

    if (diff > 1) {
        diff = 1
    }

    // value from 0 to 1 - Green to Red
    var hue = ((1 - diff) * 120).toString(10)
    return ['hsl(', hue, ',100%,50%)'].join('')
}

function setupScannedMarker(item) {
    var circleCenter = new google.maps.LatLng(item['latitude'], item['longitude'])

    var marker = new google.maps.Circle({
        map: map,
        clickable: false,
        center: circleCenter,
        radius: 70, // metres
        fillColor: getColorByDate(item['last_modified']),
        fillOpacity: 0.1,
        strokeWeight: 1,
        strokeOpacity: 0.5
    })

    return marker
}

function getColorBySpawnTime(value) {
    var now = new Date()
    var seconds = now.getMinutes() * 60 + now.getSeconds()

    // account for hour roll-over
    if (seconds < 900 && value > 2700) {
        seconds += 3600
    } else if (seconds > 2700 && value < 900) {
        value += 3600
    }

    var diff = (seconds - value)
    var hue = 275 // light purple when spawn is neither about to spawn nor active
    if (diff >= 0 && diff <= 900) { // green to red over 15 minutes of active spawn
        hue = (1 - (diff / 60 / 15)) * 120
    } else if (diff < 0 && diff > -300) { // light blue to dark blue over 5 minutes til spawn
        hue = ((1 - (-diff / 60 / 5)) * 50) + 200
    }

    hue = Math.round(hue / 5) * 5

    return hue
}

function changeSpawnIcon(color, zoom) {
    var urlColor = ''
    if (color === 275) {
        urlColor = './static/icons/hsl-275-light.png'
    } else {
        urlColor = './static/icons/hsl-' + color + '.png'
    }
    var zoomScale = 1.6 // adjust this value to change the size of the spawnpoint icons
    var minimumSize = 1
    var newSize = Math.round(zoomScale * (zoom - 10)) // this scales the icon based on zoom
    if (newSize < minimumSize) {
        newSize = minimumSize
    }

    var newIcon = {
        url: urlColor,
        scaledSize: new google.maps.Size(newSize, newSize),
        anchor: new google.maps.Point(newSize / 2, newSize / 2)
    }

    return newIcon
}

function spawnPointIndex(color) {
    var newIndex = 1
    var scale = 0
    if (color >= 0 && color <= 120) { // high to low over 15 minutes of active spawn
        scale = color / 120
        newIndex = 100 + scale * 100
    } else if (color >= 200 && color <= 250) { // low to high over 5 minutes til spawn
        scale = (color - 200) / 50
        newIndex = scale * 100
    }

    return newIndex
}

function setupSpawnpointMarker(item) {
    var circleCenter = new google.maps.LatLng(item['latitude'], item['longitude'])
    var hue = getColorBySpawnTime(item.time)
    var zoom = map.getZoom()

    var marker = new google.maps.Marker({
        map: map,
        position: circleCenter,
        icon: changeSpawnIcon(hue, zoom),
        zIndex: spawnPointIndex(hue)
    })

    marker.infoWindow = new google.maps.InfoWindow({
        content: spawnpointLabel(item),
        disableAutoPan: true,
        position: circleCenter
    })

    addListeners(marker)

    return marker
}

function clearSelection() {
    if (document.selection) {
        document.selection.empty()
    } else if (window.getSelection) {
        window.getSelection().removeAllRanges()
    }
}

function addListeners(marker) {
    marker.addListener('click', function () {
        if (!marker.infoWindowIsOpen) {
            marker.infoWindow.open(map, marker)
            clearSelection()
            updateLabelDiffTime()
            marker.persist = true
            marker.infoWindowIsOpen = true
        } else {
            marker.persist = null
            marker.infoWindow.close()
            marker.infoWindowIsOpen = false
        }
    })

    google.maps.event.addListener(marker.infoWindow, 'closeclick', function () {
        marker.persist = null
    })

    if (!isMobileDevice() && !isTouchDevice()) {
        marker.addListener('mouseover', function () {
            marker.infoWindow.open(map, marker)
            clearSelection()
            updateLabelDiffTime()
        })
    }

    marker.addListener('mouseout', function () {
        if (!marker.persist) {
            marker.infoWindow.close()
        }
    })

    return marker
}

function clearStaleMarkers() {
    $.each(mapData.pokemons, function (key, value) {
        if (mapData.pokemons[key]['disappear_time'] < new Date().getTime() ||
            excludedPokemon.indexOf(mapData.pokemons[key]['pokemon_id']) >= 0) {
            if (mapData.pokemons[key].marker.rangeCircle) {
                mapData.pokemons[key].marker.rangeCircle.setMap(null)
                delete mapData.pokemons[key].marker.rangeCircle
            }
            mapData.pokemons[key].marker.setMap(null)
            delete mapData.pokemons[key]
        }
    })

    $.each(mapData.lurePokemons, function (key, value) {
        if (mapData.lurePokemons[key]['lure_expiration'] < new Date().getTime() ||
            excludedPokemon.indexOf(mapData.lurePokemons[key]['pokemon_id']) >= 0) {
            mapData.lurePokemons[key].marker.setMap(null)
            delete mapData.lurePokemons[key]
        }
    })

    $.each(mapData.scanned, function (key, value) {
        // If older than 15mins remove
        if (mapData.scanned[key]['last_modified'] < (new Date().getTime() - 15 * 60 * 1000)) {
            mapData.scanned[key].marker.setMap(null)
            delete mapData.scanned[key]
        }
    })
}

function showInBoundsMarkers(markers, type) {
    $.each(markers, function (key, value) {
        var marker = markers[key].marker
        var show = false
        if (!markers[key].hidden) {
            if (typeof marker.getBounds === 'function') {
                if (map.getBounds().intersects(marker.getBounds())) {
                    show = true
                }
            } else if (typeof marker.getPosition === 'function') {
                if (map.getBounds().contains(marker.getPosition())) {
                    show = true
                }
            }
        }
        // marker has an associated range
        if (show && rangeMarkers.indexOf(type) !== -1) {
            // no range circle yet...let's create one
            if (!marker.rangeCircle) {
                // but only if range is active
                if (isRangeActive(map)) {
                    if (type === 'gym') marker.rangeCircle = addRangeCircle(marker, map, type, markers[key].team_id)
                    else marker.rangeCircle = addRangeCircle(marker, map, type)
                }
            } else { // there's already a range circle
                if (isRangeActive(map)) {
                    marker.rangeCircle.setMap(map)
                } else {
                    marker.rangeCircle.setMap(null)
                }
            }
        }

        if (show && !marker.getMap()) {
            marker.setMap(map)
            // Not all markers can be animated (ex: scan locations)
            if (marker.setAnimation && marker.oldAnimation) {
                marker.setAnimation(marker.oldAnimation)
            }
        } else if (!show && marker.getMap()) {
            // Not all markers can be animated (ex: scan locations)
            if (marker.getAnimation) {
                marker.oldAnimation = marker.getAnimation()
            }
            if (marker.rangeCircle) marker.rangeCircle.setMap(null)
            marker.setMap(null)
        }
    })
}

function loadRawData() {
    var loadPokemon = Store.get('showPokemon')
    var loadGyms = Store.get('showGyms')
    var loadPokestops = Store.get('showPokestops')
    var loadScanned = Store.get('showScanned')
    var loadSpawnpoints = Store.get('showSpawnpoints')
    var loadLuredOnly = Boolean(Store.get('showLuredPokestopsOnly'))

    var bounds = map.getBounds()
    var swPoint = bounds.getSouthWest()
    var nePoint = bounds.getNorthEast()
    var swLat = swPoint.lat()
    var swLng = swPoint.lng()
    var neLat = nePoint.lat()
    var neLng = nePoint.lng()

    return $.ajax({
        url: 'raw_data',
        type: 'GET',
        data: {
            'timestamp': timestamp,
            'pokemon': loadPokemon,
            'lastpokemon': lastpokemon,
            'pokestops': loadPokestops,
            'lastpokestops': lastpokestops,
            'luredonly': loadLuredOnly,
            'gyms': loadGyms,
            'lastgyms': lastgyms,
            'scanned': loadScanned,
            'lastslocs': lastslocs,
            'spawnpoints': loadSpawnpoints,
            'lastspawns': lastspawns,
            'swLat': swLat,
            'swLng': swLng,
            'neLat': neLat,
            'neLng': neLng,
            'oSwLat': oSwLat,
            'oSwLng': oSwLng,
            'oNeLat': oNeLat,
            'oNeLng': oNeLng,
            'reids': String(reincludedPokemon),
            'eids': String(excludedPokemon)
        },
        dataType: 'json',
        cache: false,
        beforeSend: function () {
            if (rawDataIsLoading) {
                return false
            } else {
                rawDataIsLoading = true
            }
        },
        error: function () {
            if (!$timeoutDialog) {
                var opts = {
                    title: 'Reduce marker settings'
                }

                $timeoutDialog = $('<div>Hmm... we\'re having problems getting data for your criteria. Try reducing what you\'re showing and zooming in to limit what\'s returned.</div>').dialog(opts)
                $timeoutDialog.dialog('open')
            } else if (!$timeoutDialog.dialog('isOpen')) {
                $timeoutDialog.dialog('open')
            }
        },
        complete: function () {
            rawDataIsLoading = false
        }
    })
}

function processPokemons(i, item) {
    if (!Store.get('showPokemon')) {
        return false // in case the checkbox was unchecked in the meantime.
    }

    if (!(item['encounter_id'] in mapData.pokemons) &&
        excludedPokemon.indexOf(item['pokemon_id']) < 0 && item['disappear_time'] > Date.now()) {
        // add marker to map and item to dict
        if (item.marker) {
            item.marker.setMap(null)
        }
        if (!item.hidden) {
            item.marker = setupPokemonMarker(item, map)
            customizePokemonMarker(item.marker, item)
            mapData.pokemons[item['encounter_id']] = item
        }
    }
}

function processPokestops(i, item) {
    if (!Store.get('showPokestops')) {
        return false
    }

    if (Store.get('showLuredPokestopsOnly') && !item['lure_expiration']) {
        return true
    }

    if (!mapData.pokestops[item['pokestop_id']]) { // new pokestop, add marker to map and item to dict
        if (item.marker && item.marker.rangeCircle) {
            item.marker.rangeCircle.setMap(null)
        }
        if (item.marker) {
            item.marker.setMap(null)
        }
        item.marker = setupPokestopMarker(item)
        mapData.pokestops[item['pokestop_id']] = item
    } else { // change existing pokestop marker to unlured/lured
        var item2 = mapData.pokestops[item['pokestop_id']]
        if (!!item['lure_expiration'] !== !!item2['lure_expiration']) {
            if (item2.marker && item2.marker.rangeCircle) {
                item2.marker.rangeCircle.setMap(null)
            }
            item2.marker.setMap(null)
            item.marker = setupPokestopMarker(item)
            mapData.pokestops[item['pokestop_id']] = item
        }
    }
}

function updatePokestops() {
    if (!Store.get('showPokestops')) {
        return false
    }

    var removeStops = []
    var currentTime = new Date().getTime()

    // change lured pokestop marker to unlured when expired
    $.each(mapData.pokestops, function (key, value) {
        if (value['lure_expiration'] && value['lure_expiration'] < currentTime) {
            value['lure_expiration'] = null
            if (value.marker && value.marker.rangeCircle) {
                value.marker.rangeCircle.setMap(null)
            }
            value.marker.setMap(null)
            value.marker = setupPokestopMarker(value)
        }
    })

    // remove unlured stops if show lured only is selected
    if (Store.get('showLuredPokestopsOnly')) {
        $.each(mapData.pokestops, function (key, value) {
            if (!value['lure_expiration']) {
                removeStops.push(key)
            }
        })
        $.each(removeStops, function (key, value) {
            if (mapData.pokestops[value] && mapData.pokestops[value].marker) {
                if (mapData.pokestops[value].marker.rangeCircle) {
                    mapData.pokestops[value].marker.rangeCircle.setMap(null)
                }
                mapData.pokestops[value].marker.setMap(null)
                delete mapData.pokestops[value]
            }
        })
    }
}

function processGyms(i, item) {
    if (!Store.get('showGyms')) {
        return false // in case the checkbox was unchecked in the meantime.
    }

    var gymLevel = getGymLevel(item.gym_points)
    var removeGymFromMap = function (gymid) {
        if (mapData.gyms[gymid] && mapData.gyms[gymid].marker) {
            if (mapData.gyms[gymid].marker.rangeCircle) {
                mapData.gyms[gymid].marker.rangeCircle.setMap(null)
            }
            mapData.gyms[gymid].marker.setMap(null)
            delete mapData.gyms[gymid]
        }
    }

    var gymHasOpenSpot = function (gymLevel, pokemonInGym) {
        return gymLevel > item.pokemon.length && item.pokemon.length !== 0
    }

    if (Store.get('showOpenGymsOnly') === 1) {
        if (!gymHasOpenSpot(gymLevel, item.pokemon.length)) {
            removeGymFromMap(item['gym_id'])
            return true
        }
    }

    if (Store.get('showOpenGymsOnly') > 1) {
        var closePrestige = 0
        switch (Store.get('showOpenGymsOnly')) {
            case 2:
                closePrestige = 1000
                break
            case 3:
                closePrestige = 2500
                break
            case 4:
                closePrestige = 5000
                break
        }

        if (!gymHasOpenSpot(gymLevel, item.pokemon.length) && (gymPrestige[gymLevel - 1] > closePrestige + item.gym_points || gymLevel === 10)) {
            removeGymFromMap(item['gym_id'])
            return true
        }
    }

    if (Store.get('showTeamGymsOnly') && Store.get('showTeamGymsOnly') !== item.team_id) {
        removeGymFromMap(item['gym_id'])
        return true
    }

    if (Store.get('showLastUpdatedGymsOnly')) {
        var now = new Date()
        if ((Store.get('showLastUpdatedGymsOnly') * 3600 * 1000) + item.last_scanned < now.getTime()) {
            removeGymFromMap(item['gym_id'])
            return true
        }
    }

    if (gymLevel < Store.get('minGymLevel')) {
        removeGymFromMap(item['gym_id'])
        return true
    }

    if (gymLevel > Store.get('maxGymLevel')) {
        removeGymFromMap(item['gym_id'])
        return true
    }

    if (item['gym_id'] in mapData.gyms) {
        item.marker = updateGymMarker(item, mapData.gyms[item['gym_id']].marker)
    } else { // add marker to map and item to dict
        item.marker = setupGymMarker(item)
    }
    mapData.gyms[item['gym_id']] = item
}

function processScanned(i, item) {
    if (!Store.get('showScanned')) {
        return false
    }

    var scanId = item['latitude'] + '|' + item['longitude']

    if (!(scanId in mapData.scanned)) { // add marker to map and item to dict
        if (item.marker) {
            item.marker.setMap(null)
        }
        item.marker = setupScannedMarker(item)
        mapData.scanned[scanId] = item
    } else {
        mapData.scanned[scanId].last_modified = item['last_modified']
    }
}

function updateScanned() {
    if (!Store.get('showScanned')) {
        return false
    }

    $.each(mapData.scanned, function (key, value) {
        if (map.getBounds().intersects(value.marker.getBounds())) {
            value.marker.setOptions({
                fillColor: getColorByDate(value['last_modified'])
            })
        }
    })
}

function processSpawnpoints(i, item) {
    if (!Store.get('showSpawnpoints')) {
        return false
    }

    var id = item['spawnpoint_id']

    if (!(id in mapData.spawnpoints)) { // add marker to map and item to dict
        if (item.marker) {
            item.marker.setMap(null)
        }
        item.marker = setupSpawnpointMarker(item)
        mapData.spawnpoints[id] = item
    }
}

function updateSpawnPoints() {
    if (!Store.get('showSpawnpoints')) {
        return false
    }

    var zoom = map.getZoom()

    $.each(mapData.spawnpoints, function (key, value) {
        if (map.getBounds().contains(value.marker.getPosition())) {
            var hue = getColorBySpawnTime(value['time'])
            value.marker.setIcon(changeSpawnIcon(hue, zoom))
            value.marker.setZIndex(spawnPointIndex(hue))
        }
    })
}

function updateMap() {
    loadRawData().done(function (result) {
        $.each(result.pokemons, processPokemons)
        $.each(result.pokestops, processPokestops)
        $.each(result.gyms, processGyms)
        $.each(result.scanned, processScanned)
        $.each(result.spawnpoints, processSpawnpoints)
        showInBoundsMarkers(mapData.pokemons, 'pokemon')
        showInBoundsMarkers(mapData.lurePokemons, 'pokemon')
        showInBoundsMarkers(mapData.gyms, 'gym')
        showInBoundsMarkers(mapData.pokestops, 'pokestop')
        showInBoundsMarkers(mapData.scanned, 'scanned')
        showInBoundsMarkers(mapData.spawnpoints, 'inbound')
        //      drawScanPath(result.scanned);
        clearStaleMarkers()

        updateScanned()
        updateSpawnPoints()
        updatePokestops()

        if ($('#stats').hasClass('visible')) {
            countMarkers(map)
        }

        oSwLat = result.oSwLat
        oSwLng = result.oSwLng
        oNeLat = result.oNeLat
        oNeLng = result.oNeLng

        lastgyms = result.lastgyms
        lastpokestops = result.lastpokestops
        lastpokemon = result.lastpokemon
        lastslocs = result.lastslocs
        lastspawns = result.lastspawns

        reids = result.reids
        if (reids instanceof Array) {
            reincludedPokemon = reids.filter(function (e) {
                return this.indexOf(e) < 0
            }, reincludedPokemon)
        }
        timestamp = result.timestamp
        lastUpdateTime = Date.now()
    })
}

function drawScanPath(points) { // eslint-disable-line no-unused-vars
    var scanPathPoints = []
    $.each(points, function (idx, point) {
        scanPathPoints.push({
            lat: point['latitude'],
            lng: point['longitude']
        })
    })
    if (scanPath) {
        scanPath.setMap(null)
    }
    scanPath = new google.maps.Polyline({
        path: scanPathPoints,
        geodesic: true,
        strokeColor: '#FF0000',
        strokeOpacity: 1.0,
        strokeWeight: 2,
        map: map
    })
}

function redrawPokemon(pokemonList) {
    var skipNotification = true
    $.each(pokemonList, function (key, value) {
        var item = pokemonList[key]
        if (!item.hidden) {
            if (item.marker.rangeCircle) item.marker.rangeCircle.setMap(null)
            var newMarker = setupPokemonMarker(item, map, this.marker.animationDisabled)
            customizePokemonMarker(newMarker, item, skipNotification)
            item.marker.setMap(null)
            pokemonList[key].marker = newMarker
        }
    })
}

var updateLabelDiffTime = function () {
    $('.label-countdown').each(function (index, element) {
        var disappearsAt = getTimeUntil(parseInt(element.getAttribute('disappears-at')))

        var hours = disappearsAt.hour
        var minutes = disappearsAt.min
        var seconds = disappearsAt.sec
        var timestring = ''

        if (disappearsAt.ttime < disappearsAt.now) {
            timestring = '(expired)'
        } else {
            timestring = '('
            if (hours > 0) {
                timestring = hours + 'h'
            }

            timestring += lpad(minutes, 2, 0) + 'm'
            timestring += lpad(seconds, 2, 0) + 's'
            timestring += ')'
        }

        $(element).text(timestring)
    })
}

function getPointDistance(pointA, pointB) {
    return google.maps.geometry.spherical.computeDistanceBetween(pointA, pointB)
}

function sendNotification(title, text, icon, lat, lng) {
    if (!('Notification' in window)) {
        return false // Notifications are not present in browser
    }

    if (Notification.permission !== 'granted') {
        Notification.requestPermission()
    } else {
        var notification = new Notification(title, {
            icon: icon,
            body: text,
            sound: 'sounds/ding.mp3'
        })

        notification.onclick = function () {
            window.focus()
            notification.close()

            centerMap(lat, lng, 20)
        }
    }
}

function createMyLocationButton() {
    var locationContainer = document.createElement('div')

    var locationButton = document.createElement('button')
    locationButton.style.backgroundColor = '#fff'
    locationButton.style.border = 'none'
    locationButton.style.outline = 'none'
    locationButton.style.width = '28px'
    locationButton.style.height = '28px'
    locationButton.style.borderRadius = '2px'
    locationButton.style.boxShadow = '0 1px 4px rgba(0,0,0,0.3)'
    locationButton.style.cursor = 'pointer'
    locationButton.style.marginRight = '10px'
    locationButton.style.padding = '0px'
    locationButton.title = 'My Location'
    locationContainer.appendChild(locationButton)

    var locationIcon = document.createElement('div')
    locationIcon.style.margin = '5px'
    locationIcon.style.width = '18px'
    locationIcon.style.height = '18px'
    locationIcon.style.backgroundImage = 'url(static/mylocation-sprite-1x.png)'
    locationIcon.style.backgroundSize = '180px 18px'
    locationIcon.style.backgroundPosition = '0px 0px'
    locationIcon.style.backgroundRepeat = 'no-repeat'
    locationIcon.id = 'current-location'
    locationButton.appendChild(locationIcon)

    locationButton.addEventListener('click', function () {
        centerMapOnLocation()
    })

    locationContainer.index = 1
    map.controls[google.maps.ControlPosition.RIGHT_BOTTOM].push(locationContainer)

    google.maps.event.addListener(map, 'dragend', function () {
        var currentLocation = document.getElementById('current-location')
        currentLocation.style.backgroundPosition = '0px 0px'
    })
}

function centerMapOnLocation() {
    var currentLocation = document.getElementById('current-location')
    var imgX = '0'
    var animationInterval = setInterval(function () {
        if (imgX === '-18') {
            imgX = '0'
        } else {
            imgX = '-18'
        }
        currentLocation.style.backgroundPosition = imgX + 'px 0'
    }, 500)
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function (position) {
            var latlng = new google.maps.LatLng(position.coords.latitude, position.coords.longitude)
            locationMarker.setPosition(latlng)
            map.setCenter(latlng)
            Store.set('followMyLocationPosition', {
                lat: position.coords.latitude,
                lng: position.coords.longitude
            })
            clearInterval(animationInterval)
            currentLocation.style.backgroundPosition = '-144px 0px'
        })
    } else {
        clearInterval(animationInterval)
        currentLocation.style.backgroundPosition = '0px 0px'
    }
}

function changeLocation(lat, lng) {
    var loc = new google.maps.LatLng(lat, lng)
    changeSearchLocation(lat, lng).done(function () {
        map.setCenter(loc)
        searchMarker.setPosition(loc)
    })
}

function changeSearchLocation(lat, lng) {
    return $.post('next_loc?lat=' + lat + '&lon=' + lng, {})
}

function centerMap(lat, lng, zoom) {
    var loc = new google.maps.LatLng(lat, lng)

    map.setCenter(loc)

    if (zoom) {
        storeZoom = false
        map.setZoom(zoom)
    }
}

function i8ln(word) {
    if ($.isEmptyObject(i8lnDictionary) && language !== 'en' && languageLookups < languageLookupThreshold) {
        $.ajax({
            url: 'static/dist/locales/' + language + '.min.json',
            dataType: 'json',
            async: false,
            success: function (data) {
                i8lnDictionary = data
            },
            error: function (jqXHR, status, error) {
                console.log('Error loading i8ln dictionary: ' + error)
                languageLookups++
            }
        })
    }
    if (word in i8lnDictionary) {
        return i8lnDictionary[word]
    } else {
        // Word doesn't exist in dictionary return it as is
        return word
    }
}

function updateGeoLocation() {
    if (navigator.geolocation && (Store.get('geoLocate') || Store.get('followMyLocation'))) {
        navigator.geolocation.getCurrentPosition(function (position) {
            var lat = position.coords.latitude
            var lng = position.coords.longitude
            var center = new google.maps.LatLng(lat, lng)

            if (Store.get('geoLocate')) {
                // the search function makes any small movements cause a loop. Need to increase resolution
                if ((typeof searchMarker !== 'undefined') && (getPointDistance(searchMarker.getPosition(), center) > 40)) {
                    $.post('next_loc?lat=' + lat + '&lon=' + lng).done(function () {
                        map.panTo(center)
                        searchMarker.setPosition(center)
                    })
                }
            }
            if (Store.get('followMyLocation')) {
                if ((typeof locationMarker !== 'undefined') && (getPointDistance(locationMarker.getPosition(), center) >= 5)) {
                    map.panTo(center)
                    locationMarker.setPosition(center)
                    Store.set('followMyLocationPosition', {
                        lat: lat,
                        lng: lng
                    })
                }
            }
        })
    }
}

function createUpdateWorker() {
    try {
        if (isMobileDevice() && (window.Worker)) {
            var updateBlob = new Blob([`onmessage = function(e) {
                var data = e.data
                if (data.name === 'backgroundUpdate') {
                    self.setInterval(function () {self.postMessage({name: 'backgroundUpdate'})}, 5000)
                }
            }`])

            var updateBlobURL = window.URL.createObjectURL(updateBlob)

            updateWorker = new Worker(updateBlobURL)

            updateWorker.onmessage = function (e) {
                var data = e.data
                if (document.hidden && data.name === 'backgroundUpdate' && Date.now() - lastUpdateTime > 2500) {
                    updateMap()
                    updateGeoLocation()
                }
            }

            updateWorker.postMessage({
                name: 'backgroundUpdate'
            })
        }
    } catch (ex) {
        console.log('Webworker error: ' + ex.message)
    }
}

function showGymDetails(id) { // eslint-disable-line no-unused-vars
    var sidebar = document.querySelector('#gym-details')
    var sidebarClose

    sidebar.classList.add('visible')

    var data = $.ajax({
        url: 'gym_data',
        type: 'GET',
        data: {
            'id': id
        },
        dataType: 'json',
        cache: false
    })

    data.done(function (result) {
        var gymLevel = getGymLevel(result.gym_points)
        var nextLvlPrestige = gymPrestige[gymLevel - 1] || 50000
        var prestigePercentage = (result.gym_points / nextLvlPrestige) * 100
        var lastScannedDate = new Date(result.last_scanned)
        var freeSlots = result.pokemon.length ? gymLevel - result.pokemon.length : 0
        var freeSlotsStr = freeSlots ? ` - ${freeSlots} Free Slots` : ''
        var gymLevelStr = ''

        if (result.team_id === 0) {
            gymLevelStr = `
                <center class="team-${result.team_id}-text">
                    <b class="team-${result.team_id}-text">Uncontested - 1 Free Slot</b>
                </center>`
        } else {
            gymLevelStr = `<div>
                <b class="team-${result.team_id}-text">Level ${gymLevel}${freeSlotsStr}</b>
            </div>`
        }
        var pokemonHtml = ''
        var headerHtml = `
            <center class="team-${result.team_id}-text">
                <div>
                    <b class="team-${result.team_id}-text">${result.name || ''}</b>
                </div>
                <img height="100px" style="padding: 5px;" src="static/forts/${gymTypes[result.team_id]}_large.png">
                <div class="prestige-bar team-${result.team_id}">
                    <div class="prestige team-${result.team_id}" style="width: ${prestigePercentage}%">
                    </div>
                </div>
                <div>
                    ${result.gym_points}/${nextLvlPrestige}
                </div>
                ${gymLevelStr}
                <div style="font-size: .7em;">
                    Last Scanned: ${lastScannedDate.getFullYear()}-${pad(lastScannedDate.getMonth() + 1)}-${pad(lastScannedDate.getDate())} ${pad(lastScannedDate.getHours())}:${pad(lastScannedDate.getMinutes())}:${pad(lastScannedDate.getSeconds())}
                </div>
                <div>
                    <a href='javascript:void(0);' onclick='javascript:openMapDirections(${result.latitude},${result.longitude});' title='View in Maps'>Get directions</a>
                </div>
            </center>
        `

        if (result.pokemon.length) {
            $.each(result.pokemon, function (i, pokemon) {
                var perfectPercent = getIv(pokemon.iv_attack, pokemon.iv_defense, pokemon.iv_stamina)
                var moveEnergy = Math.round(100 / pokemon.move_2_energy)

                pokemonHtml += `
                    <tr onclick=toggleGymPokemonDetails(this)>
                        <td width="30px">
                            <i class="pokemon-sprite n${pokemon.pokemon_id}"></i>
                        </td>
                        <td class="team-${result.team_id}-text">
                            <div style="line-height:1em;">${pokemon.pokemon_name}</div>
                            <div class="cp">CP ${pokemon.pokemon_cp}</div>
                        </td>
                        <td width="190" class="team-${result.team_id}-text" align="center">
                            <div class="trainer-level">${pokemon.trainer_level}</div>
                            <div style="line-height: 1em;">${pokemon.trainer_name}</div>
                        </td>
                        <td width="10">
                            <!--<a href="#" onclick="toggleGymPokemonDetails(this)">-->
                                <i class="team-${result.team_id}-text fa fa-angle-double-down"></i>
                            <!--</a>-->
                        </td>
                    </tr>
                    <tr class="details">
                        <td colspan="2">
                            <div class="ivs">
                                <div class="iv">
                                    <div class="type">ATK</div>
                                    <div class="value">
                                        ${pokemon.iv_attack}
                                    </div>
                                </div>
                                <div class="iv">
                                    <div class="type">DEF</div>
                                    <div class="value">
                                        ${pokemon.iv_defense}
                                    </div>
                                </div>
                                <div class="iv">
                                    <div class="type">STA</div>
                                    <div class="value">
                                        ${pokemon.iv_stamina}
                                    </div>
                                </div>
                                <div class="iv" style="width: 36px;"">
                                    <div class="type">PERFECT</div>
                                    <div class="value">
                                        ${perfectPercent.toFixed(0)}<span style="font-size: .6em;">%</span>
                                    </div>
                                </div>
                            </div>
                        </td>
                        <td colspan="2">
                            <div class="moves">
                                <div class="move">
                                    <div class="name">
                                        ${pokemon.move_1_name}
                                        <div class="type ${pokemon.move_1_type['type_en'].toLowerCase()}">${pokemon.move_1_type['type']}</div>
                                    </div>
                                    <div class="damage">
                                        ${pokemon.move_1_damage}
                                    </div>
                                </div>
                                <br>
                                <div class="move">
                                    <div class="name">
                                        ${pokemon.move_2_name}
                                        <div class="type ${pokemon.move_2_type['type_en'].toLowerCase()}">${pokemon.move_2_type['type']}</div>
                                        <div>
                                            <i class="move-bar-sprite move-bar-sprite-${moveEnergy}"></i>
                                        </div>
                                    </div>
                                    <div class="damage">
                                        ${pokemon.move_2_damage}
                                    </div>
                                </div>
                            </div>
                        </td>
                    </tr>
                    `
            })

            pokemonHtml = `<table><tbody>${pokemonHtml}</tbody></table>`
        } else if (result.team_id === 0) {
            pokemonHtml = ''
        } else {
            pokemonHtml = `
                <center class="team-${result.team_id}-text">
                    Gym Leader:<br>
                    <i class="pokemon-large-sprite n${result.guard_pokemon_id}"></i><br>
                    <b class="team-${result.team_id}-text">${result.guard_pokemon_name}</b>

                    <p style="font-size: .75em; margin: 5px;">
                        No additional gym information is available for this gym. Make sure you are collecting <a href="https://pgm.readthedocs.io/en/develop/extras/gyminfo.html">detailed gym info.</a>
                        If you have detailed gym info collection running, this gym's Pokemon information may be out of date.
                    </p>
                </center>
            `
        }

        sidebar.innerHTML = `${headerHtml}${pokemonHtml}`

        sidebarClose = document.createElement('a')
        sidebarClose.href = '#'
        sidebarClose.className = 'close'
        sidebarClose.tabIndex = 0
        sidebar.appendChild(sidebarClose)

        sidebarClose.addEventListener('click', function (event) {
            event.preventDefault()
            event.stopPropagation()
            sidebar.classList.remove('visible')
        })
    })
}

function toggleGymPokemonDetails(e) { // eslint-disable-line no-unused-vars
    e.lastElementChild.firstElementChild.classList.toggle('fa-angle-double-up')
    e.lastElementChild.firstElementChild.classList.toggle('fa-angle-double-down')
    e.nextElementSibling.classList.toggle('visible')
}

//
// Page Ready Exection
//

$(function () {
    if (!Notification) {
        console.log('could not load notifications')
        return
    }

    if (Notification.permission !== 'granted') {
        Notification.requestPermission()
    }
})

$(function () {
    // populate Navbar Style menu
    $selectStyle = $('#map-style')

    // Load Stylenames, translate entries, and populate lists
    $.getJSON('static/dist/data/mapstyle.min.json').done(function (data) {
        var styleList = []

        $.each(data, function (key, value) {
            styleList.push({
                id: key,
                text: i8ln(value)
            })
        })

        // setup the stylelist
        $selectStyle.select2({
            placeholder: 'Select Style',
            data: styleList,
            minimumResultsForSearch: Infinity
        })

        // setup the list change behavior
        $selectStyle.on('change', function (e) {
            selectedStyle = $selectStyle.val()
            map.setMapTypeId(selectedStyle)
            Store.set('map_style', selectedStyle)
        })

        // recall saved mapstyle
        $selectStyle.val(Store.get('map_style')).trigger('change')
    })

    $selectIconSize = $('#pokemon-icon-size')

    $selectIconSize.select2({
        placeholder: 'Select Icon Size',
        minimumResultsForSearch: Infinity
    })

    $selectIconSize.on('change', function () {
        Store.set('iconSizeModifier', this.value)
        redrawPokemon(mapData.pokemons)
        redrawPokemon(mapData.lurePokemons)
    })

    $selectOpenGymsOnly = $('#open-gyms-only-switch')

    $selectOpenGymsOnly.select2({
        placeholder: 'Only Show Open Gyms',
        minimumResultsForSearch: Infinity
    })

    $selectOpenGymsOnly.on('change', function () {
        Store.set('showOpenGymsOnly', this.value)
        lastgyms = false
        updateMap()
    })

    $selectTeamGymsOnly = $('#team-gyms-only-switch')

    $selectTeamGymsOnly.select2({
        placeholder: 'Only Show Gyms For Team',
        minimumResultsForSearch: Infinity
    })

    $selectTeamGymsOnly.on('change', function () {
        Store.set('showTeamGymsOnly', this.value)
        lastgyms = false
        updateMap()
    })

    $selectLastUpdateGymsOnly = $('#last-update-gyms-switch')

    $selectLastUpdateGymsOnly.select2({
        placeholder: 'Only Show Gyms Last Updated',
        minimumResultsForSearch: Infinity
    })

    $selectLastUpdateGymsOnly.on('change', function () {
        Store.set('showLastUpdatedGymsOnly', this.value)
        lastgyms = false
        updateMap()
    })

    $selectMinGymLevel = $('#min-level-gyms-filter-switch')

    $selectMinGymLevel.select2({
        placeholder: 'Minimum Gym Level',
        minimumResultsForSearch: Infinity
    })

    $selectMinGymLevel.on('change', function () {
        Store.set('minGymLevel', this.value)
        lastgyms = false
        updateMap()
    })

    $selectMaxGymLevel = $('#max-level-gyms-filter-switch')

    $selectMaxGymLevel.select2({
        placeholder: 'Maximum Gym Level',
        minimumResultsForSearch: Infinity
    })

    $selectMaxGymLevel.on('change', function () {
        Store.set('maxGymLevel', this.value)
        lastgyms = false
        updateMap()
    })

    $selectLuredPokestopsOnly = $('#lured-pokestops-only-switch')

    $selectLuredPokestopsOnly.select2({
        placeholder: 'Only Show Lured Pokestops',
        minimumResultsForSearch: Infinity
    })

    $selectLuredPokestopsOnly.on('change', function () {
        Store.set('showLuredPokestopsOnly', this.value)
        lastpokestops = false
        updateMap()
    })
    $switchGymSidebar = $('#gym-sidebar-switch')

    $switchGymSidebar.on('change', function () {
        Store.set('useGymSidebar', this.checked)
        lastgyms = false
        $.each(['gyms'], function (d, dType) {
            $.each(mapData[dType], function (key, value) {
                // for any marker you're turning off, you'll want to wipe off the range
                if (mapData[dType][key].marker.rangeCircle) {
                    mapData[dType][key].marker.rangeCircle.setMap(null)
                    delete mapData[dType][key].marker.rangeCircle
                }
                mapData[dType][key].marker.setMap(null)
            })
            mapData[dType] = {}
        })
        updateMap()
    })

    $selectSearchIconMarker = $('#iconmarker-style')
    $selectLocationIconMarker = $('#locationmarker-style')

    $.getJSON('static/dist/data/searchmarkerstyle.min.json').done(function (data) {
        searchMarkerStyles = data
        var searchMarkerStyleList = []

        $.each(data, function (key, value) {
            searchMarkerStyleList.push({
                id: key,
                text: value.name
            })
        })

        $selectSearchIconMarker.select2({
            placeholder: 'Select Icon Marker',
            data: searchMarkerStyleList,
            minimumResultsForSearch: Infinity
        })

        $selectSearchIconMarker.on('change', function (e) {
            var selectSearchIconMarker = $selectSearchIconMarker.val()
            Store.set('searchMarkerStyle', selectSearchIconMarker)
            updateSearchMarker(selectSearchIconMarker)
        })

        $selectSearchIconMarker.val(Store.get('searchMarkerStyle')).trigger('change')

        updateSearchMarker(Store.get('lockMarker'))

        $selectLocationIconMarker.select2({
            placeholder: 'Select Location Marker',
            data: searchMarkerStyleList,
            minimumResultsForSearch: Infinity
        })

        $selectLocationIconMarker.on('change', function (e) {
            Store.set('locationMarkerStyle', this.value)
            updateLocationMarker(this.value)
        })

        $selectLocationIconMarker.val(Store.get('locationMarkerStyle')).trigger('change')
    })

    $selectGymMarkerStyle = $('#gym-marker-style')

    $selectGymMarkerStyle.select2({
        placeholder: 'Select Style',
        minimumResultsForSearch: Infinity
    })

    $selectGymMarkerStyle.on('change', function (e) {
        Store.set('gymMarkerStyle', this.value)
        updateGymIcons()
    })

    $selectGymMarkerStyle.val(Store.get('gymMarkerStyle')).trigger('change')
})

$(function () {
    function formatState(state) {
        if (!state.id) {
            return state.text
        }
        var $state = $(
            '<span><i class="pokemon-sprite n' + state.element.value.toString() + '"></i> ' + state.text + '</span>'
        )
        return $state
    }

    if (Store.get('startAtUserLocation')) {
        centerMapOnLocation()
    }

    $.getJSON('static/dist/data/moves.min.json').done(function (data) {
        moves = data
    })

    $selectExclude = $('#exclude-pokemon')
    $selectPokemonNotify = $('#notify-pokemon')
    $selectRarityNotify = $('#notify-rarity')
    $textPerfectionNotify = $('#notify-perfection')
    var numberOfPokemon = 493

    // Load pokemon names and populate lists
    $.getJSON('static/dist/data/pokemon.min.json').done(function (data) {
        var pokeList = []

        $.each(data, function (key, value) {
            if (key > numberOfPokemon) {
                return false
            }
            var _types = []
            pokeList.push({
                id: key,
                text: i8ln(value['name']) + ' - #' + key
            })
            value['name'] = i8ln(value['name'])
            value['rarity'] = i8ln(value['rarity'])
            $.each(value['types'], function (key, pokemonType) {
                _types.push({
                    'type': i8ln(pokemonType['type']),
                    'color': pokemonType['color']
                })
            })
            value['types'] = _types
            idToPokemon[key] = value
        })

        // setup the filter lists
        $selectExclude.select2({
            placeholder: i8ln('Select Pokémon'),
            data: pokeList,
            templateResult: formatState
        })
        $selectPokemonNotify.select2({
            placeholder: i8ln('Select Pokémon'),
            data: pokeList,
            templateResult: formatState
        })
        $selectRarityNotify.select2({
            placeholder: i8ln('Select Rarity'),
            data: [i8ln('Common'), i8ln('Uncommon'), i8ln('Rare'), i8ln('Very Rare'), i8ln('Ultra Rare')],
            templateResult: formatState
        })

        // setup list change behavior now that we have the list to work from
        $selectExclude.on('change', function (e) {
            buffer = excludedPokemon
            excludedPokemon = $selectExclude.val().map(Number)
            buffer = buffer.filter(function (e) {
                return this.indexOf(e) < 0
            }, excludedPokemon)
            reincludedPokemon = reincludedPokemon.concat(buffer)
            clearStaleMarkers()
            Store.set('remember_select_exclude', excludedPokemon)
        })
        $selectPokemonNotify.on('change', function (e) {
            notifiedPokemon = $selectPokemonNotify.val().map(Number)
            Store.set('remember_select_notify', notifiedPokemon)
        })
        $selectRarityNotify.on('change', function (e) {
            notifiedRarity = $selectRarityNotify.val().map(String)
            Store.set('remember_select_rarity_notify', notifiedRarity)
        })
        $textPerfectionNotify.on('change', function (e) {
            notifiedMinPerfection = parseInt($textPerfectionNotify.val(), 10)
            if (isNaN(notifiedMinPerfection) || notifiedMinPerfection <= 0) {
                notifiedMinPerfection = ''
            }
            if (notifiedMinPerfection > 100) {
                notifiedMinPerfection = 100
            }
            $textPerfectionNotify.val(notifiedMinPerfection)
            Store.set('remember_text_perfection_notify', notifiedMinPerfection)
        })

        // recall saved lists
        $selectExclude.val(Store.get('remember_select_exclude')).trigger('change')
        $selectPokemonNotify.val(Store.get('remember_select_notify')).trigger('change')
        $selectRarityNotify.val(Store.get('remember_select_rarity_notify')).trigger('change')
        $textPerfectionNotify.val(Store.get('remember_text_perfection_notify')).trigger('change')

        if (isTouchDevice() && isMobileDevice()) {
            $('.select2-search input').prop('readonly', true)
        }
    })

    // run interval timers to regularly update map and timediffs
    window.setInterval(updateLabelDiffTime, 1000)
    window.setInterval(updateMap, 5000)
    window.setInterval(updateGeoLocation, 1000)

    createUpdateWorker()

    // Wipe off/restore map icons when switches are toggled
    function buildSwitchChangeListener(data, dataType, storageKey) {
        return function () {
            Store.set(storageKey, this.checked)
            if (this.checked) {
                // When switch is turned on we asume it has been off, makes sure we dont end up in limbo
                // Without this there could've been a situation where no markers are on map and only newly modified ones are loaded
                if (storageKey === 'showPokemon') {
                    lastpokemon = false
                } else if (storageKey === 'showGyms') {
                    lastgyms = false
                } else if (storageKey === 'showPokestops') {
                    lastpokestops = false
                } else if (storageKey === 'showScanned') {
                    lastslocs = false
                } else if (storageKey === 'showSpawnpoints') {
                    lastspawns = false
                }
                updateMap()
            } else {
                $.each(dataType, function (d, dType) {
                    $.each(data[dType], function (key, value) {
                        // for any marker you're turning off, you'll want to wipe off the range
                        if (data[dType][key].marker.rangeCircle) {
                            data[dType][key].marker.rangeCircle.setMap(null)
                            delete data[dType][key].marker.rangeCircle
                        }
                        if (storageKey !== 'showRanges') data[dType][key].marker.setMap(null)
                    })
                    if (storageKey !== 'showRanges') data[dType] = {}
                })
                if (storageKey === 'showRanges') {
                    updateMap()
                }
            }
        }
    }

    // Setup UI element interactions
    $('#gyms-switch').change(function () {
        var options = {
            'duration': 500
        }
        var wrapper = $('#gym-sidebar-wrapper')
        if (this.checked) {
            lastgyms = false
            wrapper.show(options)
        } else {
            lastgyms = false
            wrapper.hide(options)
        }
        var wrapper2 = $('#gyms-filter-wrapper')
        if (this.checked) {
            lastgyms = false
            wrapper2.show(options)
        } else {
            lastgyms = false
            wrapper2.hide(options)
        }
        buildSwitchChangeListener(mapData, ['gyms'], 'showGyms').bind(this)()
    })
    $('#pokemon-switch').change(function () {
        buildSwitchChangeListener(mapData, ['pokemons'], 'showPokemon').bind(this)()
    })
    $('#scanned-switch').change(function () {
        buildSwitchChangeListener(mapData, ['scanned'], 'showScanned').bind(this)()
    })
    $('#spawnpoints-switch').change(function () {
        buildSwitchChangeListener(mapData, ['spawnpoints'], 'showSpawnpoints').bind(this)()
    })
    $('#ranges-switch').change(buildSwitchChangeListener(mapData, ['gyms', 'pokemons', 'pokestops'], 'showRanges'))

    $('#pokestops-switch').change(function () {
        var options = {
            'duration': 500
        }
        var wrapper = $('#lured-pokestops-only-wrapper')
        if (this.checked) {
            lastpokestops = false
            wrapper.show(options)
        } else {
            lastpokestops = false
            wrapper.hide(options)
        }
        return buildSwitchChangeListener(mapData, ['pokestops'], 'showPokestops').bind(this)()
    })

    $('#sound-switch').change(function () {
        Store.set('playSound', this.checked)
    })

    $('#geoloc-switch').change(function () {
        $('#next-location').prop('disabled', this.checked)
        $('#next-location').css('background-color', this.checked ? '#e0e0e0' : '#ffffff')
        if (!navigator.geolocation) {
            this.checked = false
        } else {
            Store.set('geoLocate', this.checked)
        }
    })

    $('#lock-marker-switch').change(function () {
        Store.set('lockMarker', this.checked)
        searchMarker.setDraggable(!this.checked)
    })

    $('#search-switch').change(function () {
        searchControl(this.checked ? 'on' : 'off')
    })

    $('#start-at-user-location-switch').change(function () {
        Store.set('startAtUserLocation', this.checked)
    })

    $('#follow-my-location-switch').change(function () {
        if (!navigator.geolocation) {
            this.checked = false
        } else {
            Store.set('followMyLocation', this.checked)
        }
        locationMarker.setDraggable(!this.checked)
    })

    $('#scan-here-switch').change(function () {
        if (this.checked && !Store.get('scanHereAlerted')) {
            alert('Use this feature carefully ! This button will set the current map center as new search location. This may cause worker to teleport long range.')
            Store.set('scanHereAlerted', true)
        }
        $('#scan-here').toggle(this.checked)
        Store.set('scanHere', this.checked)
    })

    if ($('#nav-accordion').length) {
        $('#nav-accordion').accordion({
            active: 0,
            collapsible: true,
            heightStyle: 'content'
        })
    }

    // Initialize dataTable in statistics sidebar
    //   - turn off sorting for the 'icon' column
    //   - initially sort 'name' column alphabetically

    $('#pokemonList_table').DataTable({
        paging: false,
        searching: false,
        info: false,
        errMode: 'throw',
        'language': {
            'emptyTable': ''
        },
        'columns': [
            { 'orderable': false },
            null,
            null,
            null
        ]
    }).order([1, 'asc'])
})
