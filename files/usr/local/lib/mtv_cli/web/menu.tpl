<!--
# --------------------------------------------------------------------------
# Mediathekview auf der Kommandozeile (Webinterface)
#
# Markup für das Menü
#
# Author: Bernhard Bablok
# License: GPL3
#
# Website: https://github.com/bablokb/mtv_cli
#
# --------------------------------------------------------------------------
-->

      <div id="menu">
        <div class="pure-menu">
          <a class="pure-menu-heading" href="#">Aktionen</a>
          <ul class="pure-menu-list">
            <li class="pure-menu-item">
              <a onclick="showPart('#content_suche')"
                class="pure-menu-link">Suchen</a></li>
            <li class="pure-menu-item">
              <a onclick="updateListe()"
                class="pure-menu-link">Aktualisieren</a></li>
            <li class="pure-menu-item">
              <a onclick="downloadFilme()"
                class="pure-menu-link">Herunterladen</a></li>
            <li class="pure-menu-item">
              <a onclick="showPart('#content_edit')"
                class="pure-menu-link">Editieren</a></li>
            <li class="pure-menu-item">
              <a onclick="showStatus()"
                class="pure-menu-link">Status</a></li>
          </ul>

          <a class="pure-menu-heading" href="#">System</a>
          <ul class="pure-menu-list">
            <li class="pure-menu-item">
              <a href="phpsysinfo" target="content"
                class="pure-menu-link">Info</a></li>
            <li class="pure-menu-item">
              <a onclick="handleReboot()"
                class="pure-menu-link">Reboot</a></li>
            <li class="pure-menu-item">
              <a onclick="handleShutdown()" 
                class="pure-menu-link">Shutdown</a></li>
          </ul>

          <a class="pure-menu-heading" href="#">About</a>
          <ul class="pure-menu-list">
            <li class="pure-menu-item">
              <a onclick="onAuthorClicked()"
                class="pure-menu-link">Author</a></li>
            <li class="pure-menu-item">
              <a onclick="onLicenseClicked()"
                class="pure-menu-link">License</a></li>
            <li class="pure-menu-item">
              <a href="https://github.com/bablokb/mtv_cli" target="_blank"
                class="pure-menu-link">Projekt</a></li>
          </ul>
        </div>
