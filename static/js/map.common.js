/*eslint no-unused-vars: "off"*/

var noLabelsStyle = [{
  featureType: 'poi',
  elementType: 'labels',
  stylers: [{
    visibility: 'off'
  }]
}, {
  'featureType': 'all',
  'elementType': 'labels.text.stroke',
  'stylers': [{
    'visibility': 'off'
  }]
}, {
  'featureType': 'all',
  'elementType': 'labels.text.fill',
  'stylers': [{
    'visibility': 'off'
  }]
}, {
  'featureType': 'all',
  'elementType': 'labels.icon',
  'stylers': [{
    'visibility': 'off'
  }]
}]
var light2Style = [{
  'elementType': 'geometry',
  'stylers': [{
    'hue': '#ff4400'
  }, {
    'saturation': -68
  }, {
    'lightness': -4
  }, {
    'gamma': 0.72
  }]
}, {
  'featureType': 'road',
  'elementType': 'labels.icon'
}, {
  'featureType': 'landscape.man_made',
  'elementType': 'geometry',
  'stylers': [{
    'hue': '#0077ff'
  }, {
    'gamma': 3.1
  }]
}, {
  'featureType': 'water',
  'stylers': [{
    'hue': '#00ccff'
  }, {
    'gamma': 0.44
  }, {
    'saturation': -33
  }]
}, {
  'featureType': 'poi.park',
  'stylers': [{
    'hue': '#44ff00'
  }, {
    'saturation': -23
  }]
}, {
  'featureType': 'water',
  'elementType': 'labels.text.fill',
  'stylers': [{
    'hue': '#007fff'
  }, {
    'gamma': 0.77
  }, {
    'saturation': 65
  }, {
    'lightness': 99
  }]
}, {
  'featureType': 'water',
  'elementType': 'labels.text.stroke',
  'stylers': [{
    'gamma': 0.11
  }, {
    'weight': 5.6
  }, {
    'saturation': 99
  }, {
    'hue': '#0091ff'
  }, {
    'lightness': -86
  }]
}, {
  'featureType': 'transit.line',
  'elementType': 'geometry',
  'stylers': [{
    'lightness': -48
  }, {
    'hue': '#ff5e00'
  }, {
    'gamma': 1.2
  }, {
    'saturation': -23
  }]
}, {
  'featureType': 'transit',
  'elementType': 'labels.text.stroke',
  'stylers': [{
    'saturation': -64
  }, {
    'hue': '#ff9100'
  }, {
    'lightness': 16
  }, {
    'gamma': 0.47
  }, {
    'weight': 2.7
  }]
}]
var darkStyle = [{
  'featureType': 'all',
  'elementType': 'labels.text.fill',
  'stylers': [{
    'saturation': 36
  }, {
    'color': '#b39964'
  }, {
    'lightness': 40
  }]
}, {
  'featureType': 'all',
  'elementType': 'labels.text.stroke',
  'stylers': [{
    'visibility': 'on'
  }, {
    'color': '#000000'
  }, {
    'lightness': 16
  }]
}, {
  'featureType': 'all',
  'elementType': 'labels.icon',
  'stylers': [{
    'visibility': 'off'
  }]
}, {
  'featureType': 'administrative',
  'elementType': 'geometry.fill',
  'stylers': [{
    'color': '#000000'
  }, {
    'lightness': 20
  }]
}, {
  'featureType': 'administrative',
  'elementType': 'geometry.stroke',
  'stylers': [{
    'color': '#000000'
  }, {
    'lightness': 17
  }, {
    'weight': 1.2
  }]
}, {
  'featureType': 'landscape',
  'elementType': 'geometry',
  'stylers': [{
    'color': '#000000'
  }, {
    'lightness': 20
  }]
}, {
  'featureType': 'poi',
  'elementType': 'geometry',
  'stylers': [{
    'color': '#000000'
  }, {
    'lightness': 21
  }]
}, {
  'featureType': 'road.highway',
  'elementType': 'geometry.fill',
  'stylers': [{
    'color': '#000000'
  }, {
    'lightness': 17
  }]
}, {
  'featureType': 'road.highway',
  'elementType': 'geometry.stroke',
  'stylers': [{
    'color': '#000000'
  }, {
    'lightness': 29
  }, {
    'weight': 0.2
  }]
}, {
  'featureType': 'road.arterial',
  'elementType': 'geometry',
  'stylers': [{
    'color': '#000000'
  }, {
    'lightness': 18
  }]
}, {
  'featureType': 'road.local',
  'elementType': 'geometry',
  'stylers': [{
    'color': '#181818'
  }, {
    'lightness': 16
  }]
}, {
  'featureType': 'transit',
  'elementType': 'geometry',
  'stylers': [{
    'color': '#000000'
  }, {
    'lightness': 19
  }]
}, {
  'featureType': 'water',
  'elementType': 'geometry',
  'stylers': [{
    'lightness': 17
  }, {
    'color': '#525252'
  }]
}]
var pGoStyle = [{
  'featureType': 'landscape.man_made',
  'elementType': 'geometry.fill',
  'stylers': [{
    'color': '#a1f199'
  }]
}, {
  'featureType': 'landscape.natural.landcover',
  'elementType': 'geometry.fill',
  'stylers': [{
    'color': '#37bda2'
  }]
}, {
  'featureType': 'landscape.natural.terrain',
  'elementType': 'geometry.fill',
  'stylers': [{
    'color': '#37bda2'
  }]
}, {
  'featureType': 'poi.attraction',
  'elementType': 'geometry.fill',
  'stylers': [{
    'visibility': 'on'
  }]
}, {
  'featureType': 'poi.business',
  'elementType': 'geometry.fill',
  'stylers': [{
    'color': '#e4dfd9'
  }]
}, {
  'featureType': 'poi.business',
  'elementType': 'labels.icon',
  'stylers': [{
    'visibility': 'off'
  }]
}, {
  'featureType': 'poi.park',
  'elementType': 'geometry.fill',
  'stylers': [{
    'color': '#37bda2'
  }]
}, {
  'featureType': 'road',
  'elementType': 'geometry.fill',
  'stylers': [{
    'color': '#84b09e'
  }]
}, {
  'featureType': 'road',
  'elementType': 'geometry.stroke',
  'stylers': [{
    'color': '#fafeb8'
  }, {
    'weight': '1.25'
  }]
}, {
  'featureType': 'road.highway',
  'elementType': 'labels.icon',
  'stylers': [{
    'visibility': 'off'
  }]
}, {
  'featureType': 'water',
  'elementType': 'geometry.fill',
  'stylers': [{
    'color': '#5ddad6'
  }]
}]
var light2StyleNoLabels = [{
  'elementType': 'geometry',
  'stylers': [{
    'hue': '#ff4400'
  }, {
    'saturation': -68
  }, {
    'lightness': -4
  }, {
    'gamma': 0.72
  }]
}, {
  'featureType': 'road',
  'elementType': 'labels.icon'
}, {
  'featureType': 'landscape.man_made',
  'elementType': 'geometry',
  'stylers': [{
    'hue': '#0077ff'
  }, {
    'gamma': 3.1
  }]
}, {
  'featureType': 'water',
  'stylers': [{
    'hue': '#00ccff'
  }, {
    'gamma': 0.44
  }, {
    'saturation': -33
  }]
}, {
  'featureType': 'poi.park',
  'stylers': [{
    'hue': '#44ff00'
  }, {
    'saturation': -23
  }]
}, {
  'featureType': 'water',
  'elementType': 'labels.text.fill',
  'stylers': [{
    'hue': '#007fff'
  }, {
    'gamma': 0.77
  }, {
    'saturation': 65
  }, {
    'lightness': 99
  }]
}, {
  'featureType': 'water',
  'elementType': 'labels.text.stroke',
  'stylers': [{
    'gamma': 0.11
  }, {
    'weight': 5.6
  }, {
    'saturation': 99
  }, {
    'hue': '#0091ff'
  }, {
    'lightness': -86
  }]
}, {
  'featureType': 'transit.line',
  'elementType': 'geometry',
  'stylers': [{
    'lightness': -48
  }, {
    'hue': '#ff5e00'
  }, {
    'gamma': 1.2
  }, {
    'saturation': -23
  }]
}, {
  'featureType': 'transit',
  'elementType': 'labels.text.stroke',
  'stylers': [{
    'saturation': -64
  }, {
    'hue': '#ff9100'
  }, {
    'lightness': 16
  }, {
    'gamma': 0.47
  }, {
    'weight': 2.7
  }]
}, {
  'featureType': 'all',
  'elementType': 'labels.text.stroke',
  'stylers': [{
    'visibility': 'off'
  }]
}, {
  'featureType': 'all',
  'elementType': 'labels.text.fill',
  'stylers': [{
    'visibility': 'off'
  }]
}, {
  'featureType': 'all',
  'elementType': 'labels.icon',
  'stylers': [{
    'visibility': 'off'
  }]
}]
var darkStyleNoLabels = [{
  'featureType': 'all',
  'elementType': 'labels.text.fill',
  'stylers': [{
    'visibility': 'off'
  }]
}, {
  'featureType': 'all',
  'elementType': 'labels.text.stroke',
  'stylers': [{
    'visibility': 'off'
  }]
}, {
  'featureType': 'all',
  'elementType': 'labels.icon',
  'stylers': [{
    'visibility': 'off'
  }]
}, {
  'featureType': 'administrative',
  'elementType': 'geometry.fill',
  'stylers': [{
    'color': '#000000'
  }, {
    'lightness': 20
  }]
}, {
  'featureType': 'administrative',
  'elementType': 'geometry.stroke',
  'stylers': [{
    'color': '#000000'
  }, {
    'lightness': 17
  }, {
    'weight': 1.2
  }]
}, {
  'featureType': 'landscape',
  'elementType': 'geometry',
  'stylers': [{
    'color': '#000000'
  }, {
    'lightness': 20
  }]
}, {
  'featureType': 'poi',
  'elementType': 'geometry',
  'stylers': [{
    'color': '#000000'
  }, {
    'lightness': 21
  }]
}, {
  'featureType': 'road.highway',
  'elementType': 'geometry.fill',
  'stylers': [{
    'color': '#000000'
  }, {
    'lightness': 17
  }]
}, {
  'featureType': 'road.highway',
  'elementType': 'geometry.stroke',
  'stylers': [{
    'color': '#000000'
  }, {
    'lightness': 29
  }, {
    'weight': 0.2
  }]
}, {
  'featureType': 'road.arterial',
  'elementType': 'geometry',
  'stylers': [{
    'color': '#000000'
  }, {
    'lightness': 18
  }]
}, {
  'featureType': 'road.local',
  'elementType': 'geometry',
  'stylers': [{
    'color': '#181818'
  }, {
    'lightness': 16
  }]
}, {
  'featureType': 'transit',
  'elementType': 'geometry',
  'stylers': [{
    'color': '#000000'
  }, {
    'lightness': 19
  }]
}, {
  'featureType': 'water',
  'elementType': 'geometry',
  'stylers': [{
    'lightness': 17
  }, {
    'color': '#525252'
  }]
}]
var pGoStyleNoLabels = [{
  'featureType': 'landscape.man_made',
  'elementType': 'geometry.fill',
  'stylers': [{
    'color': '#a1f199'
  }]
}, {
  'featureType': 'landscape.natural.landcover',
  'elementType': 'geometry.fill',
  'stylers': [{
    'color': '#37bda2'
  }]
}, {
  'featureType': 'landscape.natural.terrain',
  'elementType': 'geometry.fill',
  'stylers': [{
    'color': '#37bda2'
  }]
}, {
  'featureType': 'poi.attraction',
  'elementType': 'geometry.fill',
  'stylers': [{
    'visibility': 'on'
  }]
}, {
  'featureType': 'poi.business',
  'elementType': 'geometry.fill',
  'stylers': [{
    'color': '#e4dfd9'
  }]
}, {
  'featureType': 'poi.business',
  'elementType': 'labels.icon',
  'stylers': [{
    'visibility': 'off'
  }]
}, {
  'featureType': 'poi.park',
  'elementType': 'geometry.fill',
  'stylers': [{
    'color': '#37bda2'
  }]
}, {
  'featureType': 'road',
  'elementType': 'geometry.fill',
  'stylers': [{
    'color': '#84b09e'
  }]
}, {
  'featureType': 'road',
  'elementType': 'geometry.stroke',
  'stylers': [{
    'color': '#fafeb8'
  }, {
    'weight': '1.25'
  }]
}, {
  'featureType': 'road.highway',
  'elementType': 'labels.icon',
  'stylers': [{
    'visibility': 'off'
  }]
}, {
  'featureType': 'water',
  'elementType': 'geometry.fill',
  'stylers': [{
    'color': '#5ddad6'
  }]
}, {
  'featureType': 'all',
  'elementType': 'labels.text.stroke',
  'stylers': [{
    'visibility': 'off'
  }]
}, {
  'featureType': 'all',
  'elementType': 'labels.text.fill',
  'stylers': [{
    'visibility': 'off'
  }]
}, {
  'featureType': 'all',
  'elementType': 'labels.icon',
  'stylers': [{
    'visibility': 'off'
  }]
}]
var pokemonSprites = {
  normal: {
    columns: 12,
    iconWidth: 30,
    iconHeight: 30,
    spriteWidth: 360,
    spriteHeight: 390,
    filename: 'static/icons-sprite.png',
    name: 'Normal'
  },
  highres: {
    columns: 7,
    iconWidth: 65,
    iconHeight: 65,
    spriteWidth: 455,
    spriteHeight: 1430,
    filename: 'static/icons-large-sprite.png',
    name: 'High-Res'
  },
  shuffle: {
    columns: 7,
    iconWidth: 65,
    iconHeight: 65,
    spriteWidth: 455,
    spriteHeight: 1430,
    filename: 'static/icons-shuffle-sprite.png',
    name: 'Shuffle'
  }
}

//
// LocalStorage helpers
//

var StoreTypes = {
  Boolean: {
    parse: function (str) {
      switch (str.toLowerCase()) {
        case '1':
        case 'true':
        case 'yes':
          return true
        default:
          return false
      }
    },
    stringify: function (b) {
      return b ? 'true' : 'false'
    }
  },
  JSON: {
    parse: function (str) {
      return JSON.parse(str)
    },
    stringify: function (json) {
      return JSON.stringify(json)
    }
  },
  String: {
    parse: function (str) {
      return str
    },
    stringify: function (str) {
      return str
    }
  },
  Number: {
    parse: function (str) {
      return parseInt(str, 10)
    },
    stringify: function (number) {
      return number.toString()
    }
  }
}

var StoreOptions = {
  'map_style': {
    default: 'roadmap',
    type: StoreTypes.String
  },
  'remember_select_exclude': {
    default: [],
    type: StoreTypes.JSON
  },
  'remember_select_notify': {
    default: [],
    type: StoreTypes.JSON
  },
  'remember_select_rarity_notify': {
    default: [],
    type: StoreTypes.JSON
  },
  'remember_text_perfection_notify': {
    default: '',
    type: StoreTypes.Number
  },
  'showGyms': {
    default: false,
    type: StoreTypes.Boolean
  },
  'showPokemon': {
    default: true,
    type: StoreTypes.Boolean
  },
  'showPokestops': {
    default: true,
    type: StoreTypes.Boolean
  },
  'showLuredPokestopsOnly': {
    default: 0,
    type: StoreTypes.Number
  },
  'showScanned': {
    default: false,
    type: StoreTypes.Boolean
  },
  'showSpawnpoints': {
    default: false,
    type: StoreTypes.Boolean
  },
  'showRanges': {
    default: false,
    type: StoreTypes.Boolean
  },
  'playSound': {
    default: false,
    type: StoreTypes.Boolean
  },
  'geoLocate': {
    default: false,
    type: StoreTypes.Boolean
  },
  'lockMarker': {
    default: isTouchDevice(), // default to true if touch device
    type: StoreTypes.Boolean
  },
  'startAtUserLocation': {
    default: false,
    type: StoreTypes.Boolean
  },
  'followMyLocation': {
    default: false,
    type: StoreTypes.Boolean
  },
  'followMyLocationPosition': {
    default: [],
    type: StoreTypes.JSON
  },
  'scanHere': {
    default: false,
    type: StoreTypes.Boolean
  },
  'scanHereAlerted': {
    default: false,
    type: StoreTypes.Boolean
  },
  'pokemonIcons': {
    default: 'highres',
    type: StoreTypes.String
  },
  'iconSizeModifier': {
    default: 0,
    type: StoreTypes.Number
  },
  'searchMarkerStyle': {
    default: 'google',
    type: StoreTypes.String
  },
  'locationMarkerStyle': {
    default: 'none',
    type: StoreTypes.String
  },
  'gymMarkerStyle': {
    default: 'shield',
    type: StoreTypes.String
  },
  'zoomLevel': {
    default: 16,
    type: StoreTypes.Number
  }
}

var Store = {
  getOption: function (key) {
    var option = StoreOptions[key]
    if (!option) {
      throw new Error('Store key was not defined ' + key)
    }
    return option
  },
  get: function (key) {
    var option = this.getOption(key)
    var optionType = option.type
    var rawValue = localStorage[key]
    if (rawValue === null || rawValue === undefined) {
      return option.default
    }
    var value = optionType.parse(rawValue)
    return value
  },
  set: function (key, value) {
    var option = this.getOption(key)
    var optionType = option.type || StoreTypes.String
    var rawValue = optionType.stringify(value)
    localStorage[key] = rawValue
  },
  reset: function (key) {
    localStorage.removeItem(key)
  }
}

var mapData = {
  pokemons: {},
  gyms: {},
  pokestops: {},
  lurePokemons: {},
  scanned: {},
  spawnpoints: {}
}

function getGoogleSprite (index, sprite, displayHeight) {
  displayHeight = Math.max(displayHeight, 3)
  var scale = displayHeight / sprite.iconHeight
  // Crop icon just a tiny bit to avoid bleedover from neighbor
  var scaledIconSize = new google.maps.Size(scale * sprite.iconWidth - 1, scale * sprite.iconHeight - 1)
  var scaledIconOffset = new google.maps.Point(
    (index % sprite.columns) * sprite.iconWidth * scale + 0.5,
    Math.floor(index / sprite.columns) * sprite.iconHeight * scale + 0.5)
  var scaledSpriteSize = new google.maps.Size(scale * sprite.spriteWidth, scale * sprite.spriteHeight)
  var scaledIconCenterOffset = new google.maps.Point(scale * sprite.iconWidth / 2, scale * sprite.iconHeight / 2)

  return {
    url: sprite.filename,
    size: scaledIconSize,
    scaledSize: scaledSpriteSize,
    origin: scaledIconOffset,
    anchor: scaledIconCenterOffset
  }
}

function setupPokemonMarker (item, map, isBounceDisabled) {
  // Scale icon size up with the map exponentially
  var iconSize = 2 + (map.getZoom() - 3) * (map.getZoom() - 3) * 0.2 + Store.get('iconSizeModifier')
  var pokemonIndex = item['pokemon_id'] - 1
  var sprite = pokemonSprites[Store.get('pokemonIcons')] || pokemonSprites['highres']
  var icon = getGoogleSprite(pokemonIndex, sprite, iconSize)

  var animationDisabled = false
  if (isBounceDisabled === true) {
    animationDisabled = true
  }

  var marker = new google.maps.Marker({
    position: {
      lat: item['latitude'],
      lng: item['longitude']
    },
    zIndex: 9999,
    map: map,
    icon: icon,
    animationDisabled: animationDisabled
  })

  return marker
}

function isTouchDevice () {
  // Should cover most browsers
  return 'ontouchstart' in window || navigator.maxTouchPoints
}

function isMobileDevice () {
  //  Basic mobile OS (not browser) detection
  return (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent))
}
