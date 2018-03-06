//
// Global map.js variables
//

var $selectExclude
var $selectPokemonNotify
var $selectRarityNotify
var $textPerfectionNotify
var $textLevelNotify
var $selectStyle
var $selectIconSize
var $switchOpenGymsOnly
var $switchParkGymsOnly
var $switchParkRaidGymsOnly
var $switchActiveRaidGymsOnly
var $switchRaidMinLevel
var $switchRaidMaxLevel
var $selectTeamGymsOnly
var $selectLastUpdateGymsOnly
var $selectMinGymLevel
var $selectMaxGymLevel
var $selectLuredPokestopsOnly
var $selectSearchIconMarker
var $selectLocationIconMarker
var $switchGymSidebar
var $selectExcludeRarity

const language = document.documentElement.lang === '' ? 'en' : document.documentElement.lang
var idToPokemon = {}
var i8lnDictionary = {}
var languageLookups = 0
var languageLookupThreshold = 3

var searchMarkerStyles

var timestamp
var excludedPokemon = []
var excludedPokemonByRarity = []
var excludedRarity
var notifiedPokemon = []
var notifiedRarity = []
var notifiedMinPerfection = null
var notifiedMinLevel = null

var buffer = []
var reincludedPokemon = []
var reids = []

var map
var markerCluster = window.markerCluster = {}
var rawDataIsLoading = false
var locationMarker
const rangeMarkers = ['pokemon', 'pokestop', 'gym']
var searchMarker
var storeZoom = true
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
var redrawTimeout = null

const gymTypes = ['Uncontested', 'Mystic', 'Valor', 'Instinct']

const audio = new Audio('static/sounds/ding.mp3')
const cryFileTypes = ['wav', 'mp3']

const genderType = ['♂', '♀', '⚲']
const forms = ['unset', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '!', '?', '👤', '☀️', '☔️', '⛄️', '👤', '⚔️', '🛡️', '⚡️']
const pokemonWithImages = [
    2, 3, 5, 6, 8, 9, 11, 28, 31, 34, 38, 59, 62, 65, 68, 71, 73, 76, 80, 82, 87, 89, 91, 94, 103, 105, 110, 112, 121, 123, 124, 125, 126, 129, 131, 134, 135, 136, 137, 139, 142, 143, 144, 145, 146, 150, 153, 156, 159, 160, 184, 221, 243, 244, 245, 248, 249, 250, 302, 303, 306, 320, 333, 344, 359, 361, 382, 383, 384
]

const excludedRaritiesList = [
  [],
  ['common'],
  ['common', 'uncommon'],
  ['common', 'uncommon', 'rare'],
  ['common', 'uncommon', 'rare', 'very rare'],
  ['common', 'uncommon', 'rare', 'very rare', 'ultra rare']
]

const weatherEmojis = [ '', '☀️', '☔️', '⛅', '☁️', '💨', '⛄️', '🌁' ]

/*
 text place holders:
 <pkm> - pokemon name
 <prc> - iv in percent without percent symbol
 <atk> - attack as number
 <def> - defense as number
 <sta> - stamina as number
 <lvl> - level as number
 */
var notifyIvTitle = '<pkm> <prc>% (<atk>/<def>/<sta>) (L<lvl>)'
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
    if (mapData.pokemons[encounterId].marker.infoWindowIsOpen) {
        mapData.pokemons[encounterId].marker.persist = null
        mapData.pokemons[encounterId].marker.infoWindow.close()
        mapData.pokemons[encounterId].marker.infoWindowIsOpen = false
    }
    mapData.pokemons[encounterId].marker.setMap(null)
    mapData.pokemons[encounterId].marker.setVisible(false)
    mapData.pokemons[encounterId].hidden = true
}

function createServiceWorkerReceiver() {
    navigator.serviceWorker.addEventListener('message', function (event) {
        const data = JSON.parse(event.data)
        if (data.action === 'centerMap' && data.lat && data.lon) {
            centerMap(data.lat, data.lon, 20)
        }
    })
}

function initMap() { // eslint-disable-line no-unused-vars
    map = new google.maps.Map(document.getElementById('map'), {
        center: {
            lat: Number(getParameterByName('lat')) || centerLat,
            lng: Number(getParameterByName('lon')) || centerLng
        },
        zoom: Number(getParameterByName('zoom')) || Store.get('zoomLevel'),
        gestureHandling: 'greedy',
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

    // Enable clustering.
    var clusterOptions = {
        imagePath: 'static/images/cluster/m',
        maxZoom: Store.get('maxClusterZoomLevel'),
        zoomOnClick: Store.get('clusterZoomOnClick'),
        gridSize: Store.get('clusterGridSize')
    }

    markerCluster = new MarkerClusterer(map, [], clusterOptions)

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

        // User scrolled again, reset our timeout.
        if (redrawTimeout) {
            clearTimeout(redrawTimeout)
            redrawTimeout = null
        }

        // Don't redraw constantly even if the user scrolls multiple times,
        // just add it on a timer.
        redrawTimeout = setTimeout(function () {
            redrawPokemon(mapData.pokemons)
            redrawPokemon(mapData.lurePokemons)

            // We're done processing the list. Repaint.
            markerCluster.repaint()
        }, 500)
    })

    const showSearchMarker = Store.get('showSearchMarker')
    const showLocationMarker = Store.get('showLocationMarker')
    const isLocationMarkerMovable = Store.get('isLocationMarkerMovable')

    if (showSearchMarker) {
        // Whether marker is draggable or not is set in createSearchMarker().
        searchMarker = createSearchMarker()
    }

    if (showLocationMarker) {
        locationMarker = createLocationMarker()
        locationMarker.setDraggable(isLocationMarkerMovable)
    }

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

    if (Push._agents.chrome.isSupported()) {
        createServiceWorkerReceiver()
    }
}

function updateLocationMarker(style) {
    // Don't do anything if it's disabled.
    if (!locationMarker) {
        return
    }

    if (style in searchMarkerStyles) {
        var url = searchMarkerStyles[style].icon
        if (url) {
            locationMarker.setIcon({
                url: url,
                scaledSize: new google.maps.Size(24, 24)
            })
        } else {
            locationMarker.setIcon(url)
        }
        Store.set('locationMarkerStyle', style)
    }

    // Return value is currently unused.
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
        Store.set('searchMarkerStyle', style)

        // If it's disabled, stop.
        if (!searchMarker) {
            return
        }

        var url = searchMarkerStyles[style].icon
        if (url) {
            searchMarker.setIcon({
                url: url,
                scaledSize: new google.maps.Size(24, 24)
            })
        } else {
            searchMarker.setIcon(url)
        }
    }

    return searchMarker
}

function createSearchMarker() {
    const isSearchMarkerMovable = Store.get('isSearchMarkerMovable')
    const searchMarker = new google.maps.Marker({ // need to keep reference.
        position: {
            lat: centerLat,
            lng: centerLng
        },
        map: map,
        animation: google.maps.Animation.DROP,
        draggable: !Store.get('lockMarker') && isSearchMarkerMovable,
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
    $('#gym-sidebar-wrapper').toggle(Store.get('showGyms') || Store.get('showRaids'))
    $('#gyms-filter-wrapper').toggle(Store.get('showGyms'))
    $('#team-gyms-only-switch').val(Store.get('showTeamGymsOnly'))
    $('#raids-switch').prop('checked', Store.get('showRaids'))
    $('#raid-park-gym-switch').prop('checked', Store.get('showParkRaidsOnly'))
    $('#raid-active-gym-switch').prop('checked', Store.get('showActiveRaidsOnly'))
    $('#raid-min-level-only-switch').val(Store.get('showRaidMinLevel'))
    $('#raid-max-level-only-switch').val(Store.get('showRaidMaxLevel'))
    $('#raids-filter-wrapper').toggle(Store.get('showRaids'))
    $('#open-gyms-only-switch').prop('checked', Store.get('showOpenGymsOnly'))
    $('#park-gyms-only-switch').prop('checked', Store.get('showParkGymsOnly'))
    $('#min-level-gyms-filter-switch').val(Store.get('minGymLevel'))
    $('#max-level-gyms-filter-switch').val(Store.get('maxGymLevel'))
    $('#last-update-gyms-switch').val(Store.get('showLastUpdatedGymsOnly'))
    $('#pokemon-switch').prop('checked', Store.get('showPokemon'))
    $('#pokemon-stats-switch').prop('checked', Store.get('showPokemonStats'))
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
    $('#notify-perfection-wrapper').toggle(Store.get('showPokemonStats'))
    $('#sound-switch').prop('checked', Store.get('playSound'))
    $('#pokemoncries').toggle(Store.get('playSound'))
    $('#cries-switch').prop('checked', Store.get('playCries'))
    $('#map-service-provider').val(Store.get('mapServiceProvider'))

    // Only create the Autocomplete element if it's enabled in template.
    var elSearchBox = document.getElementById('next-location')

    if (elSearchBox) {
        var searchBox = new google.maps.places.Autocomplete(elSearchBox)
        $(elSearchBox).css('background-color', $('#geoloc-switch').prop('checked') ? '#e0e0e0' : '#ffffff')

        searchBox.addListener('place_changed', function () {
            var place = searchBox.getPlace()

            if (!place.geometry) return

            var loc = place.geometry.location
            changeLocation(loc.lat(), loc.lng())
        })
    }

    if ($('#search-switch').length) {
        updateSearchStatus()
        setInterval(updateSearchStatus, 5000)
    }

    $('#pokemon-icon-size').val(Store.get('iconSizeModifier'))
}

function getTypeSpan(type) {
    return `<span style='padding: 2px 5px; text-transform: uppercase; color: white; margin-right: 2px; border-radius: 4px; font-size: 0.6em; vertical-align: middle; background-color: ${type['color']}'>${type['type']}</span>`
}

function openMapDirections(lat, lng) { // eslint-disable-line no-unused-vars
    var url = ''
    if (Store.get('mapServiceProvider') === 'googlemaps') {
        url = 'https://maps.google.com/maps?daddr=' + lat + ',' + lng
        window.open(url, '_blank')
    } else if (Store.get('mapServiceProvider') === 'applemaps') {
        url = 'https://maps.apple.com/maps?daddr=' + lat + ',' + lng
        window.open(url, '_self')
    }
}

// Converts timestamp to readable String
function getDateStr(t) {
    var dateStr = 'Unknown'
    if (t) {
        dateStr = moment(t).fromNow()
    }
    return dateStr
}

function pokemonLabel(item) {
    const pokemonRarity = getPokemonRarity(item['pokemon_id'])

    var name = item['pokemon_name']
    var rarityDisplay = pokemonRarity ? '(' + i8ln(pokemonRarity) + ')' : ''
    var types = item['pokemon_types']
    var typesDisplay = ''
    var encounterId = item['encounter_id']
    var id = item['pokemon_id']
    var latitude = item['latitude']
    var longitude = item['longitude']
    var disappearTime = item['disappear_time']
    var atk = item['individual_attack']
    var def = item['individual_defense']
    var sta = item['individual_stamina']
    var pMove1 = (moves[item['move_1']] !== undefined) ? i8ln(moves[item['move_1']]['name']) : 'gen/unknown'
    var pMove2 = (moves[item['move_2']] !== undefined) ? i8ln(moves[item['move_2']]['name']) : 'gen/unknown'
    var weight = item['weight']
    var height = item['height']
    var gender = item['gender']
    var form = item['form']
    var cp = item['cp']
    var cpMultiplier = item['cp_multiplier']
    var weatherBoostedCondition = item['weather_boosted_condition']
    var weatherDisplay = ''
    const showStats = Store.get('showPokemonStats')

    $.each(types, function (index, type) {
        typesDisplay += getTypeSpan(type)
    })

    if (weatherBoostedCondition) {
        weatherDisplay = `<span class="pokemon weather-boost">${weatherEmojis[weatherBoostedCondition]}</span>`
    }

    var details = ''

    var contentstring = ''
    var formString = ''

    if (form !== null && form > 0 && forms.length > form) {
        formString += `(${forms[item['form']]})`
    }

    contentstring += `
    <div class='pokemon name'>
      ${name} <span class='pokemon name pokedex'><a href='http://pokemon.gameinfo.io/en/pokemon/${id}' target='_blank' title='View in Pokédex'>#${id}</a></span> ${formString} <span class='pokemon gender rarity'>${genderType[gender - 1]} ${rarityDisplay}</span> ${typesDisplay} ${weatherDisplay}
    </div>`

    if (showStats && cp !== null && cpMultiplier !== null) {
        var pokemonLevel = getPokemonLevel(cpMultiplier)

        if (atk !== null && def !== null && sta !== null) {
            var iv = getIv(atk, def, sta)
        }

        contentstring += `
          <div class='pokemon container'>
            <div class='pokemon container content-left'>
              <div>
                <img class='pokemon sprite' src='static/icons/${id}.png'>
                <span class='pokemon'>Level: </span><span class='pokemon'>${pokemonLevel}</span>
                <span class='pokemon links exclude'><a href='javascript:excludePokemon(${id})'>Exclude</a></span>
                <span class='pokemon links notify'><a href='javascript:notifyAboutPokemon(${id})'>Notify</a></span>
                <span class='pokemon links remove'><a href='javascript:removePokemonMarker("${encounterId}")'>Remove</a></span>
              </div>
          </div>
          <div class='pokemon container content-right'>
            <div>
              <div class='pokemon disappear'>
                <span class='label-countdown' disappears-at='${disappearTime}'>00m00s</span> left (${moment(disappearTime).format('HH:mm')})
              </div>
              <div class='pokemon'>
                CP: <span class='pokemon encounter'>${cp}/${iv.toFixed(1)}%</span> (A${atk}/D${def}/S${sta})
              </div>
              <div class='pokemon'>
                Moveset: <span class='pokemon encounter'>${pMove1}/${pMove2}</span>
              </div>
              <div class='pokemon'>
                Weight: ${weight.toFixed(2)}kg | Height: ${height.toFixed(2)}m
              </div>
              <div>
                <span class='pokemon navigate'><a href='javascript:void(0);' onclick='javascript:openMapDirections(${latitude},${longitude});' title='Open in Google Maps'>${latitude.toFixed(6)}, ${longitude.toFixed(7)}</a></span>
              </div>
          </div>
        </div>
      </div>`
    } else {
        contentstring += `
      <div class='pokemon container'>
        <div class='pokemon container content-left'>
          <div>
            <img class='pokemon sprite' src='static/icons/${id}.png'>
            <span class='pokemon'>Level: </span><span class='pokemon no-encounter'>n/a</span>
            <span class='pokemon links exclude'><a href='javascript:excludePokemon(${id})'>Exclude</a></span>
            <span class='pokemon links notify'><a href='javascript:notifyAboutPokemon(${id})'>Notify</a></span>
            <span class='pokemon links remove'><a href='javascript:removePokemonMarker("${encounterId}")'>Remove</a></span>
          </div>
      </div>
      <div class='pokemon container content-right'>
        <div>
          <div class='pokemon disappear'>
            <span class='label-countdown' disappears-at='${disappearTime}'>00m00s</span> left (${moment(disappearTime).format('HH:mm')})
          </div>
          <div class='pokemon'>
            CP: <span class='pokemon no-encounter'>No information</span>
          </div>
          <div class='pokemon'>
            Moveset: <span class='pokemon no-encounter'>No information</span>
          </div>
          <div class='pokemon'>
            Weight: <span class='pokemon no-encounter'>n/a</span> | Height: <span class='pokemon no-encounter'>n/a</span>
          </div>
          <div>
            <span class='pokemon navigate'><a href='javascript:void(0);' onclick='javascript:openMapDirections(${latitude},${longitude});' title='Open in Google Maps'>${latitude.toFixed(6)}, ${longitude.toFixed(7)}</a></span>
          </div>
      </div>
    </div>
  </div>`
    }

    contentstring += `
      ${details}`

    return contentstring
}

function isOngoingRaid(raid) {
    return raid && Date.now() < raid.end && Date.now() > raid.start
}

function isValidRaid(raid) {
    return raid && Date.now() < raid.end && Date.now() > raid.spawn
}

function isGymSatisfiesRaidMinMaxFilter(raid) {
    if (raid) {
        return (raid['level'] <= Store.get('showRaidMaxLevel') && raid['level'] >= Store.get('showRaidMinLevel')) ? 1 : 0
    } else {
        return 0
    }
}

function gymLabel(gym, includeMembers = true) {
    const raid = gym.raid
    var raidStr = ''
    if (raid && raid.end > Date.now()) {
        if (raid.pokemon_id !== null) {
            let pMove1 = (moves[raid['move_1']] !== undefined) ? i8ln(moves[raid['move_1']]['name']) : 'unknown'
            let pMove2 = (moves[raid['move_2']] !== undefined) ? i8ln(moves[raid['move_2']]['name']) : 'unknown'

            raidStr += `
                    <div class='move'>
                      <span class='name'>${pMove1}</span><span class='type ${moves[raid['move_1']]['type'].toLowerCase()}'>${i8ln(moves[raid['move_1']]['type'])}</span>
                    </div>
                    <div class='move'>
                      <span class='name'>${pMove2}</span><span class='type ${moves[raid['move_2']]['type'].toLowerCase()}'>${i8ln(moves[raid['move_2']]['type'])}</span>
                    </div>`
        }
    }
    const lastScannedStr = getDateStr(gym.last_scanned)
    const lastModifiedStr = getDateStr(gym.last_modified)
    const slotsString = gym.slots_available ? (gym.slots_available === 1 ? '1 Free Slot' : `${gym.slots_available} Free Slots`) : 'No Free Slots'
    const teamName = gymTypes[gym.team_id]
    const isUpcomingRaid = raid != null && Date.now() < raid.start
    const isRaidStarted = isOngoingRaid(raid)
    const isRaidFilterOn = Store.get('showRaids')

    var subtitle = ''
    var image = ''
    var imageLbl = ''
    var navInfo = ''
    var memberStr = ''

    const gymPoints = gym.total_cp
    const titleText = gym.name ? gym.name : (gym.team_id === 0 ? teamName : 'Team ' + teamName)
    const title = `
      <div class='gym name'>
        <span class='team ${gymTypes[gym.team_id].toLowerCase()}'>${titleText}</span>
      </div>`

    if (gym.team_id !== 0) {
        subtitle = `
        <div>
            <img class='gym info strength' src='static/images/gym/Strength.png'>
            <span class='gym info strength'>
              Strength: ${gymPoints} (${slotsString})
            </span>
        </div>`
    }

    if ((isUpcomingRaid || isRaidStarted) && isRaidFilterOn && isGymSatisfiesRaidMinMaxFilter(raid)) {
        const raidColor = ['252,112,176', '255,158,22', '184,165,221']
        const levelStr = '★'.repeat(raid['level'])
        let raidImage = ''

        if (isRaidStarted) {
            // set Pokémon-specific image if we have one.
            if (raid.pokemon_id !== null && pokemonWithImages.indexOf(raid.pokemon_id) !== -1) {
                raidImage = `<img class='gym sprite' src='static/icons/${raid.pokemon_id}.png'>`
            } else {
                raidImage = `<img class='gym sprite' src='static/images/raid/${gymTypes[gym.team_id]}_${raid.level}_unknown.png'>`
            }
            if (raid.pokemon_id === null) {
                image = `
                    ${raidImage}
                    <div class='raid'>
                        <span style='color:rgb(${raidColor[Math.floor((raid.level - 1) / 2)]})'>
                            ${levelStr}
                        </span>
                        <span class='raid countdown label-countdown' disappears-at='${raid.end}'></span> left (${moment(raid.end).format('HH:mm')})
                    </div>
                `
            } else {
                image = `
                    <div class='raid container'>
                        <div class='raid container content-left'>
                            <div>
                                ${raidImage}
                            </div>
                        </div>
                        <div class='raid container content-right'>
                            <div>
                                <div class='raid pokemon'>
                                    ${raid['pokemon_name']} <a href='http://pokemon.gameinfo.io/en/pokemon/${raid['pokemon_id']}' target='_blank' title='View in Pokédex'>#${raid['pokemon_id']}</a> | CP: ${raid['cp']}
                                </div>
                                ${raidStr}
                            </div>
                        </div>
                    </div>
                    <div class='raid'>
                        <span style='color:rgb(${raidColor[Math.floor((raid.level - 1) / 2)]})'>
                            ${levelStr}
                        </span>
                        <span class='raid countdown label-countdown' disappears-at='${raid.end}'></span> left (${moment(raid.end).format('HH:mm')})
                    </div>
                `
            }
        } else {
            image = `<img class='gym sprite' src='static/images/gym/${gymTypes[gym.team_id]}_${getGymLevel(gym)}_${raid.level}.png'>`
        }

        if (isUpcomingRaid) {
            imageLbl = `
                <div class='raid'>
                  <span style='color:rgb(${raidColor[Math.floor((raid.level - 1) / 2)]})'>
                  ${levelStr}
                  </span>
                  Raid in <span class='raid countdown label-countdown' disappears-at='${raid.start}'> (${moment(raid.start).format('HH:mm')})</span>
                </div>`
        }
    } else {
        image = `<img class='gym sprite' src='static/images/gym/${teamName}_${getGymLevel(gym)}.png'>`
    }


    navInfo = `
            <div class='gym container'>
                <div>
                  <span class='gym info navigate'>
                    <a href='javascript:void(0);' onclick='javascript:openMapDirections(${gym.latitude},${gym.longitude});' title='Open in Google Maps'>
                      ${gym.latitude.toFixed(6)}, ${gym.longitude.toFixed(7)}
                    </a>
                  </span>
                </div>
                <div class='gym info last-scanned'>
                    Last Scanned: ${lastScannedStr}
                </div>
                <div class='gym info last-modified'>
                    Last Modified: ${lastModifiedStr}
                </div>
            </div>
        </div>`


    if (includeMembers) {
        memberStr = '<div>'

        gym.pokemon.forEach((member) => {
            memberStr += `
            <span class='gym member'>
              <center>
                <div>
                  <div>
                    <i class='pokemon-sprite n${member.pokemon_id}'></i>
                  </div>
                  <div>
                    <span class='gym pokemon'>${member.pokemon_name}</span>
                  </div>
                  <div>
                    <img class='gym pokemon motivation heart' src='static/images/gym/Heart.png'> <span class='gym pokemon motivation'>${member.cp_decayed}</span>
                  </div>
                </div>
              </center>
            </span>`
        })

        memberStr += '</div>'
    }

    return `
        <div>
            <center>
                ${title}
                ${subtitle}
                ${image}
                ${imageLbl}
            </center>
            ${navInfo}
            <center>
                ${memberStr}
            </center>
        </div>`
}

function pokestopLabel(expireTime, latitude, longitude) {
    var str
    if (expireTime) {
        str = `
            <div>
              <div class='pokestop lure'>
                Lured Pokéstop
              </div>
              <div class='pokestop-expire'>
                  <span class='label-countdown' disappears-at='${expireTime}'>00m00s</span> left (${moment(expireTime).format('HH:mm')})
              </div>
              <div>
                <img class='pokestop sprite' src='static/images/pokestop//PokestopLured.png'>
              </div>
              <div>
                <span class='pokestop navigate'><a href='javascript:void(0);' onclick='javascript:openMapDirections(${latitude},${longitude});' title='Open in Google Maps'; class='pokestop lure'>${latitude.toFixed(6)}, ${longitude.toFixed(7)}</a></span>
              </div>
            </div>
          </div>`
    } else {
        str = `
            <div>
              <div class='pokestop nolure'>
                Pokéstop
              </div>
              <div>
                <img class='pokestop sprite' src='static/images/pokestop//Pokestop.png'>
              </div>
              <div>
                <span class='pokestop navigate'><a href='javascript:void(0);' onclick='javascript:openMapDirections(${latitude},${longitude});' title='Open in Google Maps'; class='pokestop nolure'>${latitude.toFixed(6)}, ${longitude.toFixed(7)}</a></span>
              </div>
            </div>
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
        </div>`

    if (item.uncertain) {
        str += `
            <div>
                Spawn times not yet determined. Current guess ${formatSpawnTime(item.appear_time)} until ${formatSpawnTime(item.disappear_time)}
            </div>`
    } else {
        str += `
            <div>
                Every hour from ${formatSpawnTime(item.appear_time)} to ${formatSpawnTime(item.disappear_time)}
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

function getPokemonLevel(cpMultiplier) {
    if (cpMultiplier < 0.734) {
        var pokemonLevel = (58.35178527 * cpMultiplier * cpMultiplier -
        2.838007664 * cpMultiplier + 0.8539209906)
    } else {
        pokemonLevel = 171.0112688 * cpMultiplier - 95.20425243
    }
    pokemonLevel = (Math.round(pokemonLevel) * 2) / 2

    return pokemonLevel
}

function getGymLevel(gym) {
    return 6 - gym['slots_available']
}

function getRaidLevel(raid) {
    if (raid) {
        return raid['level']
    } else {
        return 0
    }
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
    var now = Date.now()
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
    var find = ['<prc>', '<pkm>', '<atk>', '<def>', '<sta>', '<lvl>']
    var pokemonlevel = (item['cp_multiplier'] !== null) ? getPokemonLevel(item['cp_multiplier']) : 0
    var replace = [((iv) ? iv.toFixed(1) : ''), item['pokemon_name'], item['individual_attack'],
        item['individual_defense'], item['individual_stamina'], pokemonlevel]
    const showStats = Store.get('showPokemonStats')
    var ntitle = repArray(((showStats && iv) ? notifyIvTitle : notifyNoIvTitle), find, replace)
    var dist = moment(item['disappear_time']).format('HH:mm:ss')
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

function playPokemonSound(pokemonID, cryFileTypes) {
    if (!Store.get('playSound')) {
        return
    }

    if (!Store.get('playCries')) {
        audio.play()
    } else {
        // Stop if we don't have any supported filetypes left.
        if (cryFileTypes.length === 0) {
            return
        }

        // Try to load the first filetype in the list.
        const filetype = cryFileTypes.shift()
        const audioCry = new Audio('static/sounds/cries/' + pokemonID + '.' + filetype)

        audioCry.play().catch(function (err) {
            // Try a different filetype.
            if (err) {
                console.log('Sound filetype %s for Pokémon %s is missing.', filetype, pokemonID)

                // If there's more left, try something else.
                playPokemonSound(pokemonID, cryFileTypes)
            }
        })
    }
}

function isNotifyPerfectionPoke(poke) {
    var hasHighAttributes = false
    var hasHighIV = false

    // Notify for IV.
    if (poke['individual_attack'] != null) {
        const perfection = getIv(poke['individual_attack'], poke['individual_defense'], poke['individual_stamina'])
        hasHighIV = notifiedMinPerfection > 0 && perfection >= notifiedMinPerfection
        const shouldNotifyForIV = (hasHighIV && notifiedMinLevel <= 0)

        hasHighAttributes = shouldNotifyForIV
    }

    // Or notify for level. If IV filter is enabled, this is an AND relation.
    if (poke['cp_multiplier'] !== null) {
        const level = getPokemonLevel(poke['cp_multiplier'])
        const hasHighLevel = notifiedMinLevel > 0 && level >= notifiedMinLevel
        const shouldNotifyForLevel = (hasHighLevel && (hasHighIV || notifiedMinPerfection <= 0))

        hasHighAttributes = hasHighAttributes || shouldNotifyForLevel
    }

    return hasHighAttributes
}

function isNotifyPoke(poke) {
    const pokemonRarity = getPokemonRarity(poke['pokemon_id'])
    const isOnNotifyList = notifiedPokemon.indexOf(poke['pokemon_id']) > -1 || notifiedRarity.indexOf(pokemonRarity) > -1
    const isNotifyPerfectionPkmn = isNotifyPerfectionPoke(poke)
    const showStats = Store.get('showPokemonStats')

    return isOnNotifyList || (showStats && isNotifyPerfectionPkmn)
}

function getNotifyPerfectionPokemons(pokemonList) {
    var notifyPerfectionPkmn = []
    $.each(pokemonList, function (key, value) {
        var item = pokemonList[key]

        if (isNotifyPerfectionPoke(item)) {
            notifyPerfectionPkmn.push(item)
        }
    })

    return notifyPerfectionPkmn
}

function customizePokemonMarker(marker, item, skipNotification) {
    var notifyText = getNotifyText(item)
    marker.addListener('click', function () {
        this.setAnimation(null)
        this.animationDisabled = true
    })

    if (!marker.rangeCircle && isRangeActive(map)) {
        marker.rangeCircle = addRangeCircle(marker, map, 'pokemon')
    }

    marker.infoWindow = new google.maps.InfoWindow({
        content: pokemonLabel(item),
        disableAutoPan: true
    })

    if (isNotifyPoke(item)) {
        if (!skipNotification) {
            playPokemonSound(item['pokemon_id'], cryFileTypes)
            sendNotification(notifyText.fav_title, notifyText.fav_text, 'static/icons/' + item['pokemon_id'] + '.png', item['latitude'], item['longitude'])
        }
        if (marker.animationDisabled !== true) {
            marker.setAnimation(google.maps.Animation.BOUNCE)
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
        map: map
    })
    marker.infoWindow = new google.maps.InfoWindow({
        content: '',
        disableAutoPan: true
    })
    updateGymMarker(item, marker)

    if (!marker.rangeCircle && isRangeActive(map)) {
        marker.rangeCircle = addRangeCircle(marker, map, 'gym', item['team_id'])
    }


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
    let raidLevel = getRaidLevel(item.raid)
    const hasActiveRaid = item.raid && item.raid.end > Date.now()
    const raidLevelVisible = raidLevel >= Store.get('showRaidMinLevel') && raidLevel <= Store.get('showRaidMaxLevel')
    const showRaidSetting = Store.get('showRaids') && (!Store.get('showActiveRaidsOnly') || !Store.get('showParkRaidsOnly'))

    if (item.raid && isOngoingRaid(item.raid) && Store.get('showRaids') && raidLevelVisible) {
        let markerImage = 'static/images/raid/' + gymTypes[item.team_id] + '_' + item.raid.level + '_unknown.png'
        if (pokemonWithImages.indexOf(item.raid.pokemon_id) !== -1) {
            markerImage = 'static/images/raid/' + gymTypes[item.team_id] + '_' + item['raid']['pokemon_id'] + '.png'
        }
        marker.setIcon({
            url: markerImage,
            scaledSize: new google.maps.Size(48, 48)
        })
        marker.setZIndex(google.maps.Marker.MAX_ZINDEX + 1)
    } else if (hasActiveRaid && raidLevelVisible && showRaidSetting) {
        marker.setIcon({
            url: 'static/images/gym/' + gymTypes[item.team_id] + '_' + getGymLevel(item) + '_' + item['raid']['level'] + '.png',
            scaledSize: new google.maps.Size(48, 48)
        })
    } else {
        marker.setIcon({
            url: 'static/images/gym/' + gymTypes[item.team_id] + '_' + getGymLevel(item) + '.png',
            scaledSize: new google.maps.Size(48, 48)
        })
        marker.setZIndex(1)
    }
    marker.infoWindow.setContent(gymLabel(item))
    return marker
}

function setupPokestopMarker(item) {
    var imagename = item['lure_expiration'] ? 'PokestopLured' : 'Pokestop'
    var image = {
        url: 'static/images/pokestop/' + imagename + '.png',
        scaledSize: new google.maps.Size(32, 32)
    }
    var marker = new google.maps.Marker({
        position: {
            lat: item['latitude'],
            lng: item['longitude']
        },
        map: map,
        zIndex: item['lure_expiration'] ? 3 : 2,
        icon: image
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
        radius: (showConfig.pokemons === true ? 70 : 450), // metres
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
    if (diff >= 0 && diff <= 1800) { // green to red over 30 minutes of active spawn
        hue = (1 - (diff / 60 / 30)) * 120
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
    var hue = getColorBySpawnTime(item.appear_time)
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
    const oldPokeMarkers = []

    $.each(mapData.pokemons, function (key, pokemon) {
        const pokemonId = pokemon['pokemon_id']
        const isPokeExpired = pokemon['disappear_time'] < Date.now()
        const isPokeExcluded = excludedPokemon.indexOf(pokemonId) !== -1
        // Limit choice to our options [0, 5].
        const excludedRarityOption = Math.min(Math.max(Store.get('excludedRarity'), 0), 5)
        const excludedRarity = excludedRaritiesList[excludedRarityOption]
        const pokemonRarity = getPokemonRarity(pokemon['pokemon_id']).toLowerCase()
        const isRarityExcluded = excludedRarity.indexOf(pokemonRarity) !== -1

        if (isPokeExpired || isPokeExcluded || isRarityExcluded) {
            const oldMarker = pokemon.marker
            const isPokeExcludedByRarity = excludedPokemonByRarity.indexOf(pokemonId) !== -1

            if (isRarityExcluded && !isPokeExcludedByRarity) {
                excludedPokemonByRarity.push(pokemonId)
            }

            if (oldMarker.rangeCircle) {
                oldMarker.rangeCircle.setMap(null)
                delete oldMarker.rangeCircle
            }

            // If it was a Pokémon w/ notification it won't be in a cluster,
            // but that doesn't matter because the MarkerClusterer will check
            // for it itself.
            oldPokeMarkers.push(oldMarker)
            oldMarker.setMap(null)
            delete mapData.pokemons[key]
            // Overwrite method to avoid all timing issues with libraries.
            oldMarker.setMap = function () {}
        }
    })

    markerCluster.removeMarkers(oldPokeMarkers, true)

    $.each(mapData.lurePokemons, function (key, lurePokemon) {
        if (lurePokemon['lure_expiration'] < new Date().getTime() ||
            excludedPokemon.indexOf(lurePokemon['pokemon_id']) >= 0) {
            lurePokemon.marker.setMap(null)
            delete mapData.lurePokemons[key]
        }
    })

    $.each(mapData.scanned, function (key, scanned) {
        // If older than 15mins remove
        if (scanned['last_modified'] < (new Date().getTime() - 15 * 60 * 1000)) {
            scanned.marker.setMap(null)
            delete mapData.scanned[key]
        }
    })
}

function showInBoundsMarkers(markers, type) {
    $.each(markers, function (key, value) {
        const item = markers[key]
        const marker = item.marker
        var show = false

        if (!item.hidden) {
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

        // Marker has an associated range.
        if (show && rangeMarkers.indexOf(type) !== -1) {
            // No range circle yet... let's create one.
            if (!marker.rangeCircle) {
                // But only if range is active.
                if (isRangeActive(map)) {
                    if (type === 'gym') marker.rangeCircle = addRangeCircle(marker, map, type, item.team_id)
                    else marker.rangeCircle = addRangeCircle(marker, map, type)
                }
            } else { // There's already a range circle.
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
    var loadGyms = (Store.get('showGyms') || Store.get('showRaids'))
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
            // Display error toast
            toastr['error']('Please check connectivity or reduce marker settings.', 'Error getting data')
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
        },
        complete: function () {
            rawDataIsLoading = false
        }
    })
}

function processPokemons(pokemon) {
    if (!Store.get('showPokemon')) {
        return false // In case the checkbox was unchecked in the meantime.
    }

    // Process Pokémon per chunk of total so we don't overwhelm the client and
    // allow redraws in between. We enable redraw in addMarkers, which doesn't
    // repaint/reset all previous markers but only draws new ones.
    processPokemonChunked(pokemon, Store.get('processPokemonChunkSize'))
}

function processPokemonChunked(pokemon, chunkSize) {
    // Early skip if we have nothing to process.
    if (typeof pokemon === 'undefined' || pokemon.length === 0) {
        return
    }

    const oldMarkers = []
    const newMarkers = []
    const chunk = pokemon.splice(-1 * chunkSize)

    $.each(chunk, function (i, poke) {
        // Early skip if we've already stored this spawn or if it's expiring
        // too soon.
        const encounterId = poke.encounter_id
        const expiringSoon = (poke.disappear_time < (Date.now() + 3000))
        if (mapData.pokemons.hasOwnProperty(encounterId) || expiringSoon) {
            return
        }

        const markers = processPokemon(poke)
        const newMarker = markers[0]
        const oldMarker = markers[1]

        // Don't add Pokémon marker to clusters if we're sending a notification.
        if (!isNotifyPoke(poke)) {
            if (newMarker) {
                newMarkers.push(newMarker)
            }

            if (oldMarker) {
                oldMarkers.push(oldMarker)
            }
        } else {
            if (newMarker) {
                newMarker.setMap(map)
            }

            if (oldMarker) {
                oldMarker.setMap(null)
            }
        }
    })

    // Disable instant redraw, we'll repaint ourselves after we've added the
    // new markers.
    markerCluster.removeMarkers(oldMarkers, true)
    markerCluster.addMarkers(newMarkers, false)

    // Any left?
    if (pokemon.length > 0) {
        setTimeout(function () {
            processPokemonChunked(pokemon, chunkSize)
        }, Store.get('processPokemonIntervalMs'))
    }
}

function processPokemon(item) {
    const isPokeExcluded = excludedPokemon.indexOf(item['pokemon_id']) !== -1
    const isPokeAlive = item['disappear_time'] > Date.now()
    // Limit choice to our options [0, 5].
    const excludedRarityOption = Math.min(Math.max(Store.get('excludedRarity'), 0), 5)
    const excludedRarity = excludedRaritiesList[excludedRarityOption]
    const pokemonRarity = getPokemonRarity(item['pokemon_id'])
    const isRarityExcluded = excludedRarity.indexOf(pokemonRarity) !== -1
    const isPokeExcludedByRarity = excludedPokemonByRarity.indexOf(item['pokemon_id']) !== -1

    var oldMarker = null
    var newMarker = null

    if (!(item['encounter_id'] in mapData.pokemons) &&
         !isPokeExcluded && !isRarityExcluded && isPokeAlive) {
        // Add marker to map and item to dict.
        if (!item.hidden) {
            const isBounceDisabled = Store.get('isBounceDisabled')
            const scaleByRarity = Store.get('scaleByRarity')
            const isNotifyPkmn = isNotifyPoke(item)

            if (item.marker) {
                updatePokemonMarker(item.marker, map, scaleByRarity, isNotifyPkmn)
            } else {
                newMarker = setupPokemonMarker(item, map, isBounceDisabled, scaleByRarity, isNotifyPkmn)
                customizePokemonMarker(newMarker, item)
                item.marker = newMarker
            }

            mapData.pokemons[item['encounter_id']] = item
        } else {
            oldMarker = item.marker
        }
    } else if (isRarityExcluded && !isPokeExcludedByRarity) {
        excludedPokemonByRarity.push(item['pokemon_id'])
    }

    return [newMarker, oldMarker]
}

function processPokestop(i, item) {
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

function processGym(i, item) {
    var gymLevel = getGymLevel(item)
    var raidLevel = getRaidLevel(item.raid)

    if (!Store.get('showGyms') && !Store.get('showRaids')) {
        return false // in case the checkbox was unchecked in the meantime.
    }

    var removeGymFromMap = function (gymid) {
        if (mapData.gyms[gymid] && mapData.gyms[gymid].marker) {
            if (mapData.gyms[gymid].marker.rangeCircle) {
                mapData.gyms[gymid].marker.rangeCircle.setMap(null)
            }
            mapData.gyms[gymid].marker.setMap(null)
            delete mapData.gyms[gymid]
        }
    }

    if (Store.get('showOpenGymsOnly')) {
        if (item.slots_available === 0) {
            removeGymFromMap(item['gym_id'])
            return true
        }
    }

    if (Store.get('showParkGymsOnly')) {
        if (!item.park) {
            removeGymFromMap(item['gym_id'])
            return true
        }
    }

    if (!Store.get('showGyms')) {
        if (Store.get('showRaids') && !isValidRaid(item.raid)) {
            removeGymFromMap(item['gym_id'])
            return true
        }

        if (Store.get('showParkRaidsOnly')) {
            if (!item.park) {
                removeGymFromMap(item['gym_id'])
                return true
            }
        }

        if (Store.get('showActiveRaidsOnly')) {
            if (!isOngoingRaid(item.raid)) {
                removeGymFromMap(item['gym_id'])
                return true
            }
        }

        if (raidLevel > Store.get('showRaidMaxLevel') || raidLevel < Store.get('showRaidMinLevel')) {
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

function processSpawnpoint(i, item) {
    if (!Store.get('showSpawnpoints')) {
        return false
    }

    var id = item['id']

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
            var hue = getColorBySpawnTime(value['appear_time'])
            value.marker.setIcon(changeSpawnIcon(hue, zoom))
            value.marker.setZIndex(spawnPointIndex(hue))
        }
    })
}

function updateMap() {
    loadRawData().done(function (result) {
        processPokemons(result.pokemons)
        $.each(result.pokestops, processPokestop)
        $.each(result.gyms, processGym)
        $.each(result.scanned, processScanned)
        $.each(result.spawnpoints, processSpawnpoint)
        // showInBoundsMarkers(mapData.pokemons, 'pokemon')
        showInBoundsMarkers(mapData.lurePokemons, 'pokemon')
        showInBoundsMarkers(mapData.gyms, 'gym')
        showInBoundsMarkers(mapData.pokestops, 'pokestop')
        showInBoundsMarkers(mapData.scanned, 'scanned')
        showInBoundsMarkers(mapData.spawnpoints, 'inbound')
        clearStaleMarkers()

        // We're done processing. Redraw.
        markerCluster.redraw()

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

function redrawPokemon(pokemonList) {
    $.each(pokemonList, function (key, value) {
        var item = pokemonList[key]

        if (!item.hidden) {
            const scaleByRarity = Store.get('scaleByRarity')
            const isNotifyPkmn = isNotifyPoke(item)

            updatePokemonMarker(item, map, scaleByRarity, isNotifyPkmn)
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
            timestring = lpad(hours, 2, 0) + ':' + lpad(minutes, 2, 0) + ':' + lpad(seconds, 2, 0)
        }

        $(element).text(timestring)
    })
}

function getPointDistance(pointA, pointB) {
    return google.maps.geometry.spherical.computeDistanceBetween(pointA, pointB)
}

function sendNotification(title, text, icon, lat, lon) {
    var notificationDetails = {
        icon: icon,
        body: text,
        data: {
            lat: lat,
            lon: lon
        }
    }

    if (Push._agents.desktop.isSupported()) {
        /* This will only run in browsers which support the old
         * Notifications API. Browsers supporting the newer Push API
         * are handled by serviceWorker.js. */
        notificationDetails.onClick = function (event) {
            if (Push._agents.desktop.isSupported()) {
                window.focus()
                event.currentTarget.close()
                centerMap(lat, lon, 20)
            }
        }
    }

    /* Push.js requests the Notification permission automatically if
     * necessary. */
    Push.create(title, notificationDetails).catch(function () {
        /* Don't do anything if the user denies the Notifications
         * permission, it means they don't want notifications. Push.js
         * will fall back to toastr if Notifications are not supported. */
    })
}

function sendToastrPokemonNotification(title, text, icon, lat, lon) {
    var notification = toastr.info(text, title, {
        closeButton: true,
        positionClass: 'toast-top-right',
        preventDuplicates: true,
        onclick: function () {
            centerMap(lat, lon, 20)
        },
        showDuration: '300',
        hideDuration: '500',
        timeOut: '6000',
        extendedTimeOut: '1500',
        showEasing: 'swing',
        hideEasing: 'linear',
        showMethod: 'fadeIn',
        hideMethod: 'fadeOut'
    })
    notification.removeClass('toast-info')
    notification.css({
        'padding-left': '74px',
        'background-image': `url('./${icon}')`,
        'background-size': '48px',
        'background-color': '#0c5952'
    })
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

            if (locationMarker) {
                locationMarker.setPosition(latlng)
            }

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

        if (searchMarker) {
            searchMarker.setPosition(loc)
        }
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
                // The search function makes any small movements cause a loop. Need to increase resolution.
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
        var pokemonHtml = ''
        if (result.pokemon.length) {
            result.pokemon.forEach((pokemon) => {
                pokemonHtml += getSidebarGymMember(pokemon)
            })

            pokemonHtml = `<table><tbody>${pokemonHtml}</tbody></table>`
        } else if (result.team_id === 0) {
            pokemonHtml = ''
        } else {
            pokemonHtml = `
                <center>
                    Gym Leader:<br>
                    <i class="pokemon-large-sprite n${result.guard_pokemon_id}"></i><br>
                    <b>${result.guard_pokemon_name}</b>

                    <p style="font-size: .75em; margin: 5px;">
                        No additional gym information is available for this gym. Make sure you are collecting <a href="https://rocketmap.readthedocs.io/en/develop/extras/gyminfo.html">detailed gym info.</a>
                        If you have detailed gym info collection running, this gym's Pokemon information may be out of date.
                    </p>
                </center>
            `
        }

        var topPart = gymLabel(result, false)
        sidebar.innerHTML = `${topPart}${pokemonHtml}`

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

function getSidebarGymMember(pokemon) {
    var perfectPercent = getIv(pokemon.iv_attack, pokemon.iv_defense, pokemon.iv_stamina)
    var moveEnergy = Math.round(100 / pokemon.move_2_energy)
    const motivationZone = ['Good', 'Average', 'Bad']
    const motivationPercentage = (pokemon.cp_decayed / pokemon.pokemon_cp) * 100
    var colorIdx = 0
    if (motivationPercentage <= 46.66) {
        colorIdx = 2
    } else if ((motivationPercentage > 46.66) && (motivationPercentage < 73.33)) {
        colorIdx = 1
    }

    // Skip getDateStr() so we can re-use the moment.js object.
    var relativeTime = 'Unknown'
    var absoluteTime = ''

    if (pokemon.deployment_time) {
        let deploymentTime = moment(pokemon.deployment_time)
        relativeTime = deploymentTime.fromNow()
        // Append as string so we show nothing when the time is Unknown.
        absoluteTime = '<div class="gym pokemon">(' + deploymentTime.format('MMM Do HH:mm') + ')</div>'
    }

    return `
                    <tr onclick=toggleGymPokemonDetails(this)>
                        <td width="30px">
                            <img class="gym pokemon sprite" src="static/icons/${pokemon.pokemon_id}.png">
                        </td>
                        <td>
                            <div class="gym pokemon"><span class="gym pokemon name">${pokemon.pokemon_name}</span></div>
                            <div>
                                <span class="gym pokemon motivation decayed zone ${motivationZone[colorIdx].toLowerCase()}">${pokemon.cp_decayed}</span>
                            </div>
                            <div>
                                <span class="gym pokemon motivation cp">Max: ${pokemon.pokemon_cp}</span>
                            </div>
                        </td>
                        <td width="190" align="center">
                            <div class="gym pokemon">${pokemon.trainer_name} (${pokemon.trainer_level})</div>
                            <div class="gym pokemon">Deployed ${relativeTime}</div>
                            ${absoluteTime}
                        </td>
                        <td width="10">
                            <!--<a href="#" onclick="toggleGymPokemonDetails(this)">-->
                                <i class="fa fa-angle-double-down"></i>
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
}

function toggleGymPokemonDetails(e) { // eslint-disable-line no-unused-vars
    e.lastElementChild.firstElementChild.classList.toggle('fa-angle-double-up')
    e.lastElementChild.firstElementChild.classList.toggle('fa-angle-double-down')
    e.nextElementSibling.classList.toggle('visible')
}

function getParameterByName(name, url) {
    if (!url) {
        url = window.location.search
    }
    name = name.replace(/[[\]]/g, '\\$&')
    var regex = new RegExp('[?&]' + name + '(=([^&#]*)|&|#|$)')
    var results = regex.exec(url)
    if (!results) {
        return null
    }
    if (!results[2]) {
        return ''
    }
    return decodeURIComponent(results[2].replace(/\+/g, ' '))
}


//
// Page Ready Execution
//

$(function () {
    /* If push.js is unsupported or disabled, fall back to toastr
     * notifications. */
    Push.config({
        serviceWorker: 'serviceWorker.min.js',
        fallback: function (notification) {
            sendToastrPokemonNotification(
                notification.title,
                notification.body,
                notification.icon,
                notification.data.lat,
                notification.data.lon
            )
        }
    })
})

$(function () {
    /* TODO: Some items are being loaded asynchronously, but synchronous code
     * depends on it. Restructure to make sure these "loading" tasks are
     * completed before continuing. Right now it "works" because the first
     * map update is scheduled after 5s. */

    // populate Navbar Style menu
    $selectStyle = $('#map-style')

    // Load dynamic rarity.
    updatePokemonRarities()

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

    var mapServiceProvider = $('#map-service-provider')

    mapServiceProvider.select2({
        placeholder: 'Select map provider',
        data: ['googlemaps', 'applemaps'],
        minimumResultsForSearch: Infinity
    })

    mapServiceProvider.on('change', function (e) {
        var selectedVal = mapServiceProvider.val()
        Store.set('mapServiceProvider', selectedVal)
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

        // We're done processing the list. Repaint.
        markerCluster.repaint()
    })

    $switchOpenGymsOnly = $('#open-gyms-only-switch')

    $switchOpenGymsOnly.on('change', function () {
        Store.set('showOpenGymsOnly', this.checked)
        lastgyms = false
        updateMap()
    })

    $switchParkGymsOnly = $('#park-gyms-only-switch')

    $switchParkGymsOnly.on('change', function () {
        Store.set('showParkGymsOnly', this.checked)
        lastgyms = false
        updateMap()
    })

    $switchParkRaidGymsOnly = $('#raid-park-gym-switch')

    $switchParkRaidGymsOnly.on('change', function () {
        Store.set('showParkRaidsOnly', this.checked)
        lastgyms = false
        updateMap()
    })

    $switchActiveRaidGymsOnly = $('#raid-active-gym-switch')

    $switchActiveRaidGymsOnly.on('change', function () {
        Store.set('showActiveRaidsOnly', this.checked)
        lastgyms = false
        updateMap()
    })

    $switchRaidMinLevel = $('#raid-min-level-only-switch')

    $switchRaidMinLevel.select2({
        placeholder: 'Minimum raid level',
        minimumResultsForSearch: Infinity
    })

    $switchRaidMinLevel.on('change', function () {
        Store.set('showRaidMinLevel', this.value)
        lastgyms = false
        updateMap()
    })

    $switchRaidMaxLevel = $('#raid-max-level-only-switch')

    $switchRaidMaxLevel.select2({
        placeholder: 'Maximum raid level',
        minimumResultsForSearch: Infinity
    })

    $switchRaidMaxLevel.on('change', function () {
        Store.set('showRaidMaxLevel', this.value)
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

    $selectExcludeRarity = $('#exclude-rarity')

    $selectExcludeRarity.select2({
        placeholder: 'None',
        minimumResultsForSearch: Infinity
    })

    $selectExcludeRarity.on('change', function () {
        Store.set('excludedRarity', this.value)
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
})

$(function () {
    moment.locale(language)
    function formatState(state) {
        if (!state.id) {
            return state.text
        }
        var $state = $(
            '<span><i class="pokemon-sprite n' + state.element.value.toString() + '"></i> ' + state.text + '</span>'
        )
        return $state
    }

    if (Store.get('startAtUserLocation') && getParameterByName('lat') == null && getParameterByName('lon') == null) {
        centerMapOnLocation()
    }

    $.getJSON('static/dist/data/moves.min.json').done(function (data) {
        moves = data
    })

    $selectExclude = $('#exclude-pokemon')
    $selectExcludeRarity = $('#exclude-rarity')
    $selectPokemonNotify = $('#notify-pokemon')
    $selectRarityNotify = $('#notify-rarity')
    $textPerfectionNotify = $('#notify-perfection')
    $textLevelNotify = $('#notify-level')
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
        $selectExcludeRarity.on('change', function (e) {
            excludedRarity = $selectExcludeRarity.val()
            reincludedPokemon = reincludedPokemon.concat(excludedPokemonByRarity)
            excludedPokemonByRarity = []
            clearStaleMarkers()
            Store.set('excludedRarity', excludedRarity)
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
        $textLevelNotify.on('change', function (e) {
            notifiedMinLevel = parseInt($textLevelNotify.val(), 10)
            if (isNaN(notifiedMinLevel) || notifiedMinLevel <= 0) {
                notifiedMinLevel = ''
            }
            if (notifiedMinLevel > 35) {
                notifiedMinLevel = 35
            }
            $textLevelNotify.val(notifiedMinLevel)
            Store.set('remember_text_level_notify', notifiedMinLevel)
        })

        // recall saved lists
        $selectExclude.val(Store.get('remember_select_exclude')).trigger('change')
        $selectExcludeRarity.val(Store.get('excludedRarity')).trigger('change')
        $selectPokemonNotify.val(Store.get('remember_select_notify')).trigger('change')
        $selectRarityNotify.val(Store.get('remember_select_rarity_notify')).trigger('change')
        $textPerfectionNotify.val(Store.get('remember_text_perfection_notify')).trigger('change')
        $textLevelNotify.val(Store.get('remember_text_level_notify')).trigger('change')

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
                } else if (storageKey === 'showPokestops') {
                    lastpokestops = false
                } else if (storageKey === 'showScanned') {
                    lastslocs = false
                } else if (storageKey === 'showSpawnpoints') {
                    lastspawns = false
                }
                updateMap()
            } else if (storageKey === 'showGyms' || storageKey === 'showRaids') {
                // if any of switch is enable then do not remove gyms markers, only update them
                if (Store.get('showGyms') || Store.get('showRaids')) {
                    lastgyms = false
                    updateMap()
                } else {
                    $.each(dataType, function (d, dType) {
                        $.each(data[dType], function (key, value) {
                            // for any marker you're turning off, you'll want to wipe off the range
                            if (data[dType][key].marker.rangeCircle) {
                                data[dType][key].marker.rangeCircle.setMap(null)
                                delete data[dType][key].marker.rangeCircle
                            }
                            data[dType][key].marker.setMap(null)
                        })
                        data[dType] = {}
                    })
                }
            } else {
                $.each(dataType, function (d, dType) {
                    var oldPokeMarkers = []
                    $.each(data[dType], function (key, value) {
                        // for any marker you're turning off, you'll want to wipe off the range
                        if (data[dType][key].marker.rangeCircle) {
                            data[dType][key].marker.rangeCircle.setMap(null)
                            delete data[dType][key].marker.rangeCircle
                        }
                        if (storageKey !== 'showRanges') {
                            data[dType][key].marker.setMap(null)
                            if (dType === 'pokemons') {
                                oldPokeMarkers.push(data[dType][key].marker)
                            }
                        }
                    })
                    // If the type was "pokemons".
                    if (oldPokeMarkers.length > 0) {
                        markerCluster.removeMarkers(oldPokeMarkers)
                    }
                    if (storageKey !== 'showRanges') data[dType] = {}
                })
                if (storageKey === 'showRanges') {
                    updateMap()
                }
            }
        }
    }

    function resetGymFilter() {
        Store.set('showTeamGymsOnly', 0)
        Store.set('minGymLevel', 0)
        Store.set('maxGymLevel', 6)
        Store.set('showOpenGymsOnly', false)
        Store.set('showParkGymsOnly', false)

        $('#team-gyms-only-switch').val(Store.get('showTeamGymsOnly'))
        $('#open-gyms-only-switch').prop('checked', Store.get('showOpenGymsOnly'))
        $('#park-gyms-only-switch').prop('checked', Store.get('showParkGymsOnly'))
        $('#min-level-gyms-filter-switch').val(Store.get('minGymLevel'))
        $('#max-level-gyms-filter-switch').val(Store.get('maxGymLevel'))

        $('#team-gyms-only-switch').trigger('change')
        $('#min-level-gyms-filter-switch').trigger('change')
        $('#max-level-gyms-filter-switch').trigger('change')
    }

    // Setup UI element interactions
    $('#gyms-switch').change(function () {
        var options = {
            'duration': 500
        }
        resetGymFilter()
        var wrapperGyms = $('#gyms-filter-wrapper')
        var switchRaids = $('#raids-switch')
        var wrapperSidebar = $('#gym-sidebar-wrapper')
        if (this.checked) {
            lastgyms = false
            wrapperGyms.show(options)
            wrapperSidebar.show(options)
        } else {
            lastgyms = false
            wrapperGyms.hide(options)
            if (!switchRaids.prop('checked')) {
                wrapperSidebar.hide(options)
            }
        }
        buildSwitchChangeListener(mapData, ['gyms'], 'showGyms').bind(this)()
    })
    $('#raids-switch').change(function () {
        var options = {
            'duration': 500
        }
        var wrapperRaids = $('#raids-filter-wrapper')
        var switchGyms = $('#gyms-switch')
        var wrapperSidebar = $('#gym-sidebar-wrapper')
        if (this.checked) {
            lastgyms = false
            wrapperRaids.show(options)
            wrapperSidebar.show(options)
        } else {
            lastgyms = false
            wrapperRaids.hide(options)
            if (!switchGyms.prop('checked')) {
                wrapperSidebar.hide(options)
            }
        }
        buildSwitchChangeListener(mapData, ['gyms'], 'showRaids').bind(this)()
    })
    $('#pokemon-switch').change(function () {
        buildSwitchChangeListener(mapData, ['pokemons'], 'showPokemon').bind(this)()
        markerCluster.repaint()
    })
    $('#pokemon-stats-switch').change(function () {
        Store.set('showPokemonStats', this.checked)
        var options = {
            'duration': 500
        }
        const $wrapper = $('#notify-perfection-wrapper')
        if (this.checked) {
            $wrapper.show(options)
        } else {
            $wrapper.hide(options)
        }
        updatePokemonLabels(mapData.pokemons)
        // Only redraw Pokémon which are notified of perfection.
        var notifyPerfectionPkmn = getNotifyPerfectionPokemons(mapData.pokemons)
        redrawPokemon(notifyPerfectionPkmn)

        markerCluster.redraw()
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
        var options = {
            'duration': 500
        }
        var criesWrapper = $('#pokemoncries')
        if (this.checked) {
            criesWrapper.show(options)
        } else {
            criesWrapper.hide(options)
        }
    })

    $('#cries-switch').change(function () {
        Store.set('playCries', this.checked)
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

        if (searchMarker) {
            searchMarker.setDraggable(!this.checked)
        }
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

        if (locationMarker) {
            if (this.checked) {
                // Follow our position programatically, so no dragging.
                locationMarker.setDraggable(false)
            } else {
                // Go back to default non-follow.
                const isMarkerMovable = Store.get('isLocationMarkerMovable')
                locationMarker.setDraggable(isMarkerMovable)
            }
        }
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
