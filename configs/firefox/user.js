
/*
Mozilla User Preferences
THIS FILE WILL OVERRIDE prefs.js
If you make changes to this file while the application is running,
the changes will be overwritten when the application exits.

To change a preference value, you can either:
- modify it via the UI (e.g. via about:config in the browser); or
- set it within a user.js file in your profile.
*/


/*
NOTE TO SELF:
setting default zoom to 133% is not possible through about:config values as it's stored in a database
may be easier to just automate this change somehow rather than copy over the database file for one config
or just auto-open a tab for about:preferences because it takes 2 seconds to flip manually

The user.js should be stored in the Firefox profile folder, located in
    ~/.mozilla/firefox/<rand_string>.default-release/
*/


/*
+--------------------
    Performance
+--------------------
*/

/*
force enable hardware acceleration (experimental)
*/
user_pref("layers.acceleration.force-enabled", true);
/*
force enable webrender engine (experimental)
*/
user_pref("gfx.webrender.all", true);
/*
set engine FPS to 170 (my fastest monitor) manually
*/
user_pref("layout.frame_rate", 170);


/* 
+--------------------
    Customization
+--------------------
*/

/*
Toolbar customization
*/
user_pref("browser.uiCustomization.state", '{"placements":{"widget-overflow-fixed-list":[],"unified-extensions-area":["_contain-facebook-browser-action","chrome-gnome-shell_gnome_org-browser-action","enhancerforyoutube_maximerf_addons_mozilla_org-browser-action","sponsorblocker_ajay_app-browser-action"],"nav-bar":["back-button","forward-button","stop-reload-button","plugin_okta_com-browser-action","urlbar-container","downloads-button","fxa-toolbar-menu-button","ublock0_raymondhill_net-browser-action","_446900e4-71c2-419f-a6a7-df9c091e268b_-browser-action"],"toolbar-menubar":["menubar-items"],"TabsToolbar":["firefox-view-button","tabbrowser-tabs","new-tab-button","alltabs-button"],"PersonalToolbar":["import-button","personal-bookmarks"]},"seen":["save-to-pocket-button","developer-button","ublock0_raymondhill_net-browser-action","enhancerforyoutube_maximerf_addons_mozilla_org-browser-action","chrome-gnome-shell_gnome_org-browser-action","_contain-facebook-browser-action","_036a55b4-5e72-4d05-a06c-cba2dfcc134a_-browser-action","_9bbf6724-d709-492e-a313-bfed0415a224_-browser-action","_44df5123-f715-9146-bfaa-c6e8d4461d44_-browser-action","plugin_okta_com-browser-action","_3b56bcc7-54e5-44a2-9b44-66c3ef58c13e_-browser-action","_446900e4-71c2-419f-a6a7-df9c091e268b_-browser-action","sponsorblocker_ajay_app-browser-action"],"dirtyAreaCache":["nav-bar","PersonalToolbar","TabsToolbar","unified-extensions-area"],"currentVersion":19,"newElementCount":4}');

/*
New Tab Page shortcuts
At full screen 2x8 = 16 shortcuts
At half screen 2x6 = 12 shortcuts
*/
user_pref("browser.newtabpage.pinned", '[{"url":"https://amazon.com/","label":"amazon","baseDomain":"amazon.com"},{"url":"https://mail.google.com/mail/u/0/#inbox","label":"mail"},{"url":"https://www.facebook.com/","label":"facebook","baseDomain":"facebook.com"},{"url":"https://twitter.com/","label":"twitter","baseDomain":"twitter.com"},{"url":"https://www.instagram.com/","label":"instagram","baseDomain":"instagram.com"},{"url":"https://www.reddit.com/","label":"reddit","baseDomain":"reddit.com"},{"url":"https://www.youtube.com/","label":"youtube","baseDomain":"youtube.com"},{"url":"https://keep.google.com/","label":"notes","baseDomain":"keep.google.com"},{"url":"https://www.phoronix.com/scan.php?page=home","baseDomain":"phoronix.com"},{"url":"https://chat.openai.com/chat","label":"chatgpt","baseDomain":"openai.com"},{"url":"http://192.168.50.2:8080","label":"vue","baseDomain":"192.168.50.2"},{"url":"http://lichess.org","label":"lichess","baseDomain":"lichess.org"},{"url":"https://app.ynab.com","label":"ynab","baseDomain":"ynab.com"},{"url":"https://app.plex.tv/desktop/#!/","label":"app.plex","baseDomain":"app.plex.tv"},{"url":"http://192.168.50.2","label":"nas","baseDomain":"192.168.50.2"},{"url":"https://www.protondb.com/","label":"proton","baseDomain":"protondb.com"}]');
