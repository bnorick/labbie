![Labbie Logo](https://github.com/bnorick/labbie/blob/master/docs/logo.png)

--------------------------------------------------------------------------------

Labbie is a tool to help you determine which bases to use for each enchant in the Eternal Labyrinth.

Features include:
- Manual lookup for enchants and bases
- Summary of all enchants and bases
- Screen capture lookup for enchants at the end of Lab

All character information is pulled daily from [poe.ninja](https://poe.ninja/) for [SC trade](https://poe.ninja/challenge/builds), which amounts to 5-15 GB per day depending on how long the league has been running. The enchant specific information is extracted and stored in Azure blob for users of Labbie, preventing too much load on poe.ninja and reducing the amount of data that Labbie itself downloads to just 1-2 MB per day.

Additional features, such as enchant statistics, will be coming in the future. If you have ideas or specific requests, please submit an issue so I can track them more easily.

Labbie was written to use on the Windows operating system, so YMMV if you choose to try with other operating systems (and I don't currently have plans to produce releases for other operating systems).

## Installation
To install Labbie, download the latest release from the [releases page](https://github.com/bnorick/labbie/releases). Simply extract the `Labbie.zip` file (not the source code) and run `Labbie.exe`.

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