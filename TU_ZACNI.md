## Inštalácia na Linuxe

Nasledujúce pokyny boli navrhnuté pre Ubuntu/Debian, ale mali by sa dať ľahko prispôsobiť aj pre iné distribúcie Linuxu.

### Rýchla inštalácia

> **Poznámka**
> Aby ste predišli konfliktom s inými balíkmi a neporiadku vo vašom pythonovskom prostredí, odporúčame pre ChipWhisperer použiť virtuálne prostredie (virtual environment). Nezabudnite toto virtuálne prostredie aktivovať pred každým spustením Pythonu alebo Jupyteru!

Ak sa ponáhľate a používate Ubuntu, spustenie nasledujúcich príkazov a následný reštart systému by vás mali rýchlo dostať do prevádzky:

```bash
sudo apt update && sudo apt upgrade

sudo apt install make git avr-libc gcc-avr \
    gcc-arm-none-eabi libusb-1.0-0-dev usbutils curl

#moze tu vyskocit error pri instalovani packagov, na ktory treba pouzit apt --fix-broken a skusit to znovu

curl -Ls https://astral.sh/uv/install.sh | sh
source ~/.bashrc

cd ~/
git clone https://github.com/nvimpel/chipwhisperer.git
cd chipwhisperer


uv venv ~/.cwvenv --python 3.12
source ~/.cwvenv/bin/activate

sudo cp 50-newae.rules /etc/udev/rules.d/50-newae.rules
sudo udevadm control --reload-rules
sudo groupadd -fr chipwhisperer
sudo usermod -aG chipwhisperer $USER
sudo usermod -aG plugdev $USER

uv pip install --upgrade pip
uv pip install -e .
uv pip install -r jupyter/requirements.txt

```
Po dokončení spustíte pomocou 
```bash
source ~/.cwvenv/bin/activate
cd ~/chipwhisperer
jupyter notebook
```
