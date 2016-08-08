
# Copy supervisor files to ~/supervisor for first install or to reset (deleting supervisord.conf)
if [ ! -f ~/supervisor/supervisord.conf ]; then
  cp supervisord.conf ~/supervisor/supervisord.conf
  cp gen-workers.sh ~/supervisor/gen-workers.sh
  cp template.ini ~/supervisor/template.ini
fi
if [ -f ~/supervisor/supervisord.conf ]; then
  echo "If you want to start over please run this command:"
  echo "rm $home/supervisor/supervisord.conf"
  echo "Then re run this script"
fi
