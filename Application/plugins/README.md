



The brief note to the architecture being implemented in Plugins 

Requirements:
    An abstract class which defines what all must be defined by the plugin, plugin has to subclass this, 
    to check whatever conditions has been fulfilled.

    1. Every datasource should have a permission key defined in the config, this permission key will have 
        name of the permission and the tables or table associted with it.
        Name: Name of the plugin 


    2. An API through which users can provide permissions to plugins, these permissions should be stored in 
        a common sqlite table called as permissions. This API should give name of all the tables currently
        datapod have, the users will select the table names.
    

    3. A decorator on every api call of the plugin, this will check what all permissions has been given to this plugin, 
        if no permissions is present raise an exception with  an error to the users for permission.

    4. Intialize a data path for this plugin in the beginning, Only this path will be accessible to this plugin, nothing else never.
    
    5. Read plugins from the top level plugin directory, check if the exported classs is instance of abstract class PluginConfiguration,
        if not dont integrate this plugin, if any condition fails dont integrate this plugin 

    6. Permission module will have permissions corresponding to every Plugins.
        For all the 
    
