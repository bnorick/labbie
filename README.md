![Labbie Logo](https://github.com/bnorick/labbie/blob/master/docs/logo.png)

--------------------------------------------------------------------------------

Labbie is a tool to help you determine which bases to use for each enchant in the Eternal Labyrinth.

Features include:
- Manual lookup for enchants and bases
- Summary of all enchants and bases
- Screen capture lookup for enchants at the end of Lab

All enchant information is pulled daily from [poe.ninja](https://poe.ninja/) from both [SC trade](https://poe.ninja/challenge/builds) and [daily builds](https://poe.ninja/daily/builds) (currently this amounts to around 5GB per day). The enchant specific information is extracted and stored in Azure blob for users of Labbie, preventing too much load on poe.ninja.

Additional features, such as enchant statistics, will be coming in the future.

Labbie was written to use on the Windows operating system, so YMMV if you choose to try with other operating systems (and I don't currently have plans to produce releases for other operating systems).

## Settings
You can choose whether to show results for league, daily, or both.

A hotkey can be set for screen capture, I use \` (backtick). Additionally, modifier and function keys can be specified, e.g., `shift+q` or `F1`.

The default screen capture configuration is for **1920x1080** fullscreen windowed. For 2560x1440 resolution, you can use `left=450, top=277, right=1225, bottom=616`. You can set your own screen capture area by manually entering the pixel offsets in the corresponding text boxes or interactively using the "Select" button in the settings window. The screen capture area should be aligned as in the following example:

![Screen Capture Area Example](https://github.com/bnorick/labbie/blob/master/docs/screen_capture_area.png)

## Support Development
Labbie requires me to host the enchant data myself, which I am doing out of my pocket. If you use the tool and love it, please consider a small donation through [Paypal](https://www.paypal.com/donate?hosted_button_id=4QXG9CPFYF5UJ) or become a patron through [Patreon](https://www.patreon.com/bnorick).

## License
For historical reasons, the source code for Labbie is dually licensed under the GPLv3 and MIT licenses. Originally, Labbie was released with PyQt5, which is licensed under the GPLv3 and thus necessitated the use of that license. More recently, Labbie switched to PySide2 and began to offer the MIT license a second licensing option.

Other components in this repository, namely the updater and packaging source, is licensed under the MIT license.

Several pieces of source code have been used from other open source libraries and the licenses which apply to them are noted inline (or alongside, in the case of qtmodern).

<div>The Labbie icon was made by <a href="https://www.freepik.com" title="Freepik">Freepik</a> from <a href="https://www.flaticon.com/" title="Flaticon">www.flaticon.com</a>.</div>