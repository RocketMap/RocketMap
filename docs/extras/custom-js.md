# Custom.js
RocketMap supports the use of a custom JavaScript file to run custom code instead of editing core files.

## Warning of using code you don't understand
Never just put code in custom.js unless you understand what it does, someone could give you malicious JavaScript code that could result in credentials (accounts and keys) being stolen!

Please do not copy/paste code from strangers online!

## Use of custom.js
Place your custom code into 'custom.js' in the folder 'static/js'. *Examples are found in 'static/js/custom.js.example'.*

### Examples
Examples for a MOTD, google analytics and disabling scaling icons by rarity are included in custom.js.example!
The example below is how to set default options usually done by editing core files.

* **Set a new map style by default.**  
First we set a variable for it and pick which style we want as default.
```
const map_style = 'satellite'
```
Next we have to tell the script to store the value to set it.
```
Store.set('map_style', map_style)
```

Whenever you edit custom.js you will have to run `npm run build` to set the changes.
When you load the map it will be set to satellite as default.

Setting options in this way forces that setting on page load, so even if a user changes the setting it will revert back to what you have set in custom.js every time, keep this in mind when forcing settings.  

If you don't want to revert back to what you have set in custom.js every time, you can do it like in the example below.  

* **Add default Pokémon to "Hide Pokémon".**  
First we need to retrieve what has already been set so we don't overwrite anything excluded in the interface. Then add the Pokémon we want to hide by default **by adding the Pokémon IDs to the excludedPokemon-array, e.g. [13, 16] as shown in the example below**. Finally we have to tell the script to store the value to set it.

```
const totalExcluded = Store.get('remember_select_exclude') // Retrieve what has already been set.

const excludedPokemon = [13, 16] // Add Pokémon IDs separated by commas (e.g. [1, 2, 3])

// If the new default Pokémon doesn't exist then add it to the list.
excludedPokemon.forEach((id) => {
    if (totalExcluded.indexOf(id) === -1) {
        totalExcluded.push(id)
    }
})

Store.set('remember_select_exclude', totalExcluded) // Tell the script to store the value to set it.
``` 
When you load the map Weedle and Pidgey will be hidden as default.

See 'custom.js.example' for more information.
