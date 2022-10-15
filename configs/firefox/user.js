// Mozilla User Preferences
// THIS FILE WILL OVERRIDE prefs.js
// If you make changes to this file while the application is running,
// the changes will be overwritten when the application exits.
//
// To change a preference value, you can either:
// - modify it via the UI (e.g. via about:config in the browser); or
// - set it within a user.js file in your profile.



// NOTE TO SELF:
// setting default zoom to 133% is not possible through about:config values as it's stored in a database
// may be easier to just automate this change somehow rather than copy over the database file for one config
// or just auto-open a tab for about:preferences because it takes 2 seconds to flip manually

//  The user.js should be stored in the Firefox profile folder, located in
//      ~/.mozilla/firefox/<rand_string>.default-release/




// ########################################
// [EXPERIMENTAL] PERFORMANCE OPTIMIZATIONS
// ########################################
// force enable hardware acceleration
user_pref("layers.acceleration.force-enabled", true);
// force enable webrender engine
user_pref("gfx.webrender.all", true);

// set engine FPS to 170 (my fastest monitor) manually
user_pref("layout.frame_rate", 170);


// ########################################
// CUSTOMIZATION
// ########################################
// toolbar cutomization
user_pref("browser.uiCustomization.state", "{\"placements\":{\"widget-overflow-fixed-list\":[],\"nav-bar\":[\"back-button\",\"forward-button\",\"stop-reload-button\",\"urlbar-container\",\"downloads-button\",\"fxa-toolbar-menu-button\",\"ublock0_raymondhill_net-browser-action\",\"_446900e4-71c2-419f-a6a7-df9c091e268b_-browser-action\",\"plugin_okta_com-browser-action\"],\"TabsToolbar\":[\"tabbrowser-tabs\",\"new-tab-button\",\"alltabs-button\"],\"PersonalToolbar\":[\"import-button\",\"personal-bookmarks\"]},\"seen\":[\"save-to-pocket-button\",\"developer-button\",\"ublock0_raymondhill_net-browser-action\",\"enhancerforyoutube_maximerf_addons_mozilla_org-browser-action\",\"chrome-gnome-shell_gnome_org-browser-action\",\"_contain-facebook-browser-action\",\"_036a55b4-5e72-4d05-a06c-cba2dfcc134a_-browser-action\",\"_9bbf6724-d709-492e-a313-bfed0415a224_-browser-action\",\"_44df5123-f715-9146-bfaa-c6e8d4461d44_-browser-action\",\"plugin_okta_com-browser-action\",\"_3b56bcc7-54e5-44a2-9b44-66c3ef58c13e_-browser-action\",\"_446900e4-71c2-419f-a6a7-df9c091e268b_-browser-action\",\"sponsorblocker_ajay_app-browser-action\"],\"dirtyAreaCache\":[\"nav-bar\",\"PersonalToolbar\",\"TabsToolbar\"],\"currentVersion\":17,\"newElementCount\":3}");
// newtabpage shortcuts
user_pref("browser.newtabpage.pinned", "[{\"url\":\"https://smile.amazon.com/gp/chpf/homepage/ref=smi_chpf_redirect?ie=UTF8&%2AVersion%2A=1&%2Aentries%2A=0\",\"label\":\"amazon\",\"baseDomain\":\"smile.amazon.com\"},{\"url\":\"https://mail.google.com/mail/u/0/#inbox\",\"label\":\"mail\"},{\"url\":\"https://www.facebook.com/\",\"label\":\"facebook\",\"baseDomain\":\"facebook.com\"},{\"url\":\"https://twitter.com/\",\"label\":\"twitter\",\"baseDomain\":\"twitter.com\"},{\"url\":\"https://www.instagram.com/\",\"label\":\"instagram\",\"baseDomain\":\"instagram.com\"},{\"url\":\"https://www.reddit.com/\",\"label\":\"reddit\",\"baseDomain\":\"reddit.com\"},{\"url\":\"https://www.youtube.com/\",\"label\":\"youtube\",\"baseDomain\":\"youtube.com\"},{\"url\":\"https://keep.google.com/\",\"label\":\"keep.google\",\"baseDomain\":\"keep.google.com\"},{\"url\":\"https://app.plex.tv/desktop/#!/\",\"label\":\"app.plex\",\"baseDomain\":\"app.plex.tv\"},{\"url\":\"https://www.phoronix.com/scan.php?page=home\",\"baseDomain\":\"phoronix.com\"},{\"url\":\"http://192.168.1.64\",\"label\":\"vault\",\"baseDomain\":\"192.168.50.49\"},{\"url\":\"http://192.168.50.49:8080\",\"label\":\"vuetorrent\",\"baseDomain\":\"192.168.1.64\"},{\"url\":\"https://www.protondb.com/\",\"label\":\"proton\",\"baseDomain\":\"protondb.com\"}]");