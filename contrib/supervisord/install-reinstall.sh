# Check to see if ~/supervisor exists
if [ ! -d ~/supervisor ]; then
  mkdir -p ~/supervisor
fi

if [ -f ~/supervisor/supervisord.conf ]; then
  echo "If you want to start over please run this command:"
  echo "rm $HOME/supervisor/supervisord.conf"
  echo "Then re run this script"
fi

# Copy supervisor files to ~/supervisor for first install or to reset (deleting supervisord.conf)
if [ ! -f ~/supervisor/supervisord.conf ]; then
  cp supervisord.conf ~/supervisor/supervisord.conf
  cp gen-workers.sh ~/supervisor/gen-workers.sh
  cp template.ini ~/supervisor/template.ini
  echo "Complete! Please run:"
  echo "cd $HOME/supervisor"
fi
