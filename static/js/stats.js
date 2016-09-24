function countMarkers (map) { // eslint-disable-line no-unused-vars
  document.getElementById('stats-ldg-label').innerHTML = ''
  document.getElementById('stats-pkmn-label').innerHTML = 'Pokémon'
  document.getElementById('stats-gym-label').innerHTML = 'Gyms'
  document.getElementById('stats-pkstop-label').innerHTML = 'PokéStops'

  var i = 0
  var arenaCount = []
  var arenaTotal = 0
  var pkmnCount = []
  var pkmnTotal = 0
  var pokestopCount = []
  var pokestopTotal = 0
  var pokeStatTable = $('#pokemonList_table').DataTable()

  // Bounds of the currently visible map
  var currentVisibleMap = map.getBounds()

  // Is a particular Pokémon/Gym/Pokéstop within the currently visible map?
  var thisPokeIsVisible = false
  var thisGymIsVisible = false
  var thisPokestopIsVisible = false

  if (Store.get('showPokemon')) {
    $.each(mapData.pokemons, function (key, value) {
      var thisPokeLocation = { lat: mapData.pokemons[key]['latitude'], lng: mapData.pokemons[key]['longitude'] }
      thisPokeIsVisible = currentVisibleMap.contains(thisPokeLocation)

      if (thisPokeIsVisible) {
        pkmnTotal++
        if (pkmnCount[mapData.pokemons[key]['pokemon_id']] === 0 || !pkmnCount[mapData.pokemons[key]['pokemon_id']]) {
          pkmnCount[mapData.pokemons[key]['pokemon_id']] = {
            'ID': mapData.pokemons[key]['pokemon_id'],
            'Count': 1,
            'Name': mapData.pokemons[key]['pokemon_name']
          }
        } else {
          pkmnCount[mapData.pokemons[key]['pokemon_id']].Count += 1
        }
      }
    })

    var pokeCounts = []

    for (i = 0; i < pkmnCount.length; i++) {
      if (pkmnCount[i] && pkmnCount[i].Count > 0) {
        pokeCounts.push(
          [
            '<img src=\'static/icons/' + pkmnCount[i].ID + '.png\' />',
            '<a href=\'http://www.pokemon.com/us/pokedex/' + pkmnCount[i].ID + '\' target=\'_blank\' title=\'View in Pokédex\' style=\'color: black;\'>' + pkmnCount[i].Name + '</a>',
            pkmnCount[i].Count,
            (Math.round(pkmnCount[i].Count * 100 / pkmnTotal * 10) / 10) + '%'
          ]
        )
      }
    }

    // Clear stale data, add fresh data, redraw

    $('#pokemonList_table').dataTable().show()
    pokeStatTable
      .clear()
      .rows.add(pokeCounts)
      .draw()
  } else {
    pokeStatTable
      .clear()
      .draw()

    document.getElementById('pokeStatStatus').innerHTML = 'Pokémon markers are disabled'
    $('#pokemonList_table').dataTable().hide()
  }   // end Pokémon processing

  // begin Gyms processing
  if (Store.get('showGyms')) {
    $.each(mapData.gyms, function (key, value) {
      var thisGymLocation = { lat: mapData.gyms[key]['latitude'], lng: mapData.gyms[key]['longitude'] }
      thisGymIsVisible = currentVisibleMap.contains(thisGymLocation)

      if (thisGymIsVisible) {
        arenaTotal++
        if (arenaCount[mapData.gyms[key]['team_id']] === 0 || !arenaCount[mapData.gyms[key]['team_id']]) {
          arenaCount[mapData.gyms[key]['team_id']] = 1
        } else {
          arenaCount[mapData.gyms[key]['team_id']] += 1
        }
      }
    })

    var arenaListString = '<table><th>Icon</th><th>Team Color</th><th>Count</th><th>%</th><tr><td></td><td>Total</td><td>' + arenaTotal + '</td></tr>'
    for (i = 0; i < arenaCount.length; i++) {
      if (arenaCount[i] > 0) {
        if (i === 1) {
          arenaListString += '<tr><td><img src="static/forts/Mystic.png" /></td><td>' + 'Blue' + '</td><td>' + arenaCount[i] + '</td><td>' + Math.round(arenaCount[i] * 100 / arenaTotal * 10) / 10 + '%</td></tr>'
        } else if (i === 2) {
          arenaListString += '<tr><td><img src="static/forts/Valor.png" /></td><td>' + 'Red' + '</td><td>' + arenaCount[i] + '</td><td>' + Math.round(arenaCount[i] * 100 / arenaTotal * 10) / 10 + '%</td></tr>'
        } else if (i === 3) {
          arenaListString += '<tr><td><img src="static/forts/Instinct.png" /></td><td>' + 'Yellow' + '</td><td>' + arenaCount[i] + '</td><td>' + Math.round(arenaCount[i] * 100 / arenaTotal * 10) / 10 + '%</td></tr>'
        } else {
          arenaListString += '<tr><td><img src="static/forts/Uncontested.png" /></td><td>' + 'Clear' + '</td><td>' + arenaCount[i] + '</td><td>' + Math.round(arenaCount[i] * 100 / arenaTotal * 10) / 10 + '%</td></tr>'
        }
      }
    }
    arenaListString += '</table>'
    document.getElementById('arenaList').innerHTML = arenaListString
  } else {
    document.getElementById('arenaList').innerHTML = 'Gyms markers are disabled'
  }

  if (Store.get('showPokestops')) {
    $.each(mapData.pokestops, function (key, value) {
      var thisPokestopLocation = { lat: mapData.pokestops[key]['latitude'], lng: mapData.pokestops[key]['longitude'] }
      thisPokestopIsVisible = currentVisibleMap.contains(thisPokestopLocation)

      if (thisPokestopIsVisible) {
        if (mapData.pokestops[key]['lure_expiration'] && mapData.pokestops[key]['lure_expiration'] > 0) {
          if (pokestopCount[1] === 0 || !pokestopCount[1]) {
            pokestopCount[1] = 1
          } else {
            pokestopCount[1] += 1
          }
        } else {
          if (pokestopCount[0] === 0 || !pokestopCount[0]) {
            pokestopCount[0] = 1
          } else {
            pokestopCount[0] += 1
          }
        }
        pokestopTotal++
      }
    })
    var pokestopListString = '<table><th>Icon</th><th>Status</th><th>Count</th><th>%</th><tr><td></td><td>Total</td><td>' + pokestopTotal + '</td></tr>'
    for (i = 0; i < pokestopCount.length; i++) {
      if (pokestopCount[i] > 0) {
        if (i === 0) {
          pokestopListString += '<tr><td><img src="static/forts/Pstop.png" /></td><td>' + 'Not Lured' + '</td><td>' + pokestopCount[i] + '</td><td>' + Math.round(pokestopCount[i] * 100 / pokestopTotal * 10) / 10 + '%</td></tr>'
        } else if (i === 1) {
          pokestopListString += '<tr><td><img src="static/forts/PstopLured.png" /></td><td>' + 'Lured' + '</td><td>' + pokestopCount[i] + '</td><td>' + Math.round(pokestopCount[i] * 100 / pokestopTotal * 10) / 10 + '%</td></tr>'
        }
      }
    }
    pokestopListString += '</table>'
    document.getElementById('pokestopList').innerHTML = pokestopListString
  } else {
    document.getElementById('pokestopList').innerHTML = 'PokéStops markers are disabled'
  }
}
