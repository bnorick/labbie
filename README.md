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

## Installation
To install Labbie, all you need to do is downloading the latest stable release [here](https://github.com/bnorick/labbie/releases), extracting the archive to any location on your computer and start it by excecuting the "Labbie.exe".

## Settings
You can choose whether to show results for league, daily, or both.

A hotkey can be set for screen capture, I use \` (backtick). Additionally, modifier and function keys can be specified, e.g., `shift+q` or `F1`.

The default screen capture configuration is for **1920x1080** fullscreen windowed. For 2560x1440 resolution, you can use `left=450, top=277, right=1225, bottom=616`. You can set your own screen capture area by manually entering the pixel offsets in the corresponding text boxes or interactively using the "Select" button in the settings window. The screen capture area should be aligned as in the following example:

![Screen Capture Area Example](https://github.com/bnorick/labbie/blob/master/docs/screen_capture_area.png)

## Support Development
Labbie requires me to host the enchant data myself, which I am doing out of my pocket. If you use the tool and love it, please consider a small donation through [Paypal](https://www.paypal.com/donate?hosted_button_id=4QXG9CPFYF5UJ) or become a patron through [Patreon](https://www.patreon.com/bnorick).

## License
The GPLv3 license (see the [LICENSE](LICENSE) file) applies to all source code for Labbie which is not otherwise licensed under a compatible license.

<div>The Labbie icon was made by <a href="https://www.freepik.com" title="Freepik">Freepik</a> from <a href="https://www.flaticon.com/" title="Flaticon">www.flaticon.com</a>.</div>
