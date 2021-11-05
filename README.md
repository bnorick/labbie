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

## Configuration
Labbie has some minimal configuration (with more to come in the future) which is currently accessible only by editing the config files in [config](config). A UI for configuration is a current TODO.

Most importantly, OCR bounds (where Labbie looks for enchants on your screen) need to be set relative to your whole monitor (with 0, 0 being at the top left). This configuration is [here](https://github.com/bnorick/labbie/blob/6b3f000628a481f50a46b587902b5454abc8e490/config/config.toml#L8) in [config/config.toml](config/config.toml). The default configuration is for **1920x1080** fullscreen windowed, but the line below may be uncommented (and the initial line commented) for 1440p resolution monitors. If you have any other setup (including simply windowed mode), you'll need to figure out what bounds to use for OCR support to function.

By default, the \` (backtick) is used as a hotkey for OCR. To disable the hotkey, set `ocr = ''`. You may also use other hotkeys such as `ocr = 'shift+q'` or `ocr = 'F1'`.

## Support Development
Labbie requires me to host the enchant data myself, which I am doing out of my pocket. If you use the tool and love it, please consider a small donation through [Paypal](https://www.paypal.com/donate?hosted_button_id=4QXG9CPFYF5UJ) or become a patron through [Patreon](https://www.patreon.com/bnorick).

## License
The GPLv3 license (see the [LICENSE](LICENSE) file) applies to all source code for Labbie which is not otherwise licensed under a compatible license.

<div>The Labbie icon was made by <a href="https://www.freepik.com" title="Freepik">Freepik</a> from <a href="https://www.flaticon.com/" title="Flaticon">www.flaticon.com</a>.</div>