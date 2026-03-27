# Debugging Checklist

## Blank Screen Or Nothing Renders

- Confirm `new Phaser.Game(config)` is actually constructed.
- Confirm the configured `parent` element exists in the DOM.
- Confirm at least one scene starts and reaches `create()`.
- Confirm the camera is not looking at empty space because of bad positions or
  bounds.
- Check the browser console first. A single uncaught exception during `create()`
  often leaves only a blank canvas.

## Assets Fail To Load

- Check the browser network panel for 404s and incorrect relative paths.
- Confirm the asset is loaded before first use.
- Confirm asset keys match exactly, including case.
- Confirm production builds still serve assets from the same logical path as the
  dev server.
- If `setPath()` or `baseURL` is used, verify the final resolved URL instead of
  assuming it.

## Scene Bugs

- Confirm the intended scene is started, not only added to the manager.
- Confirm overlays launched with `run()` or `launch()` are not accidentally
  duplicated.
- Confirm scene-level listeners are not registered again on every restart.
- Use `shutdown` and `destroy` cleanup for timers, events, tweens, and
  cross-scene subscriptions when they should not survive a restart.

## Input Problems

- Confirm interactive objects actually call `setInteractive()`.
- Confirm another object or overlay is not sitting above the target in the
  input stack.
- Confirm focus-sensitive keyboard input still works after tab switches or UI
  overlays.
- If mixing DOM UI and Phaser input, confirm the DOM layer is not intercepting
  pointer events unintentionally.

## Physics Problems

- Confirm physics is enabled for the scene or game.
- Confirm the object has the expected Arcade body type and size.
- Confirm body offsets, collision boxes, and sprite origins line up visually.
- Confirm `collider` versus `overlap` matches the intended behavior.
- Turn on temporary Arcade debug rendering when body positions or sizes are
  unclear.

## Scale And Resize Problems

- Confirm the selected scale mode matches the requested layout model.
- Confirm the parent container has the expected CSS size.
- Confirm `resize()` versus `setGameSize()` is used for the correct scale mode.
- Confirm DOM overlays still align with the canvas after resizing.

## Final Validation

- Reproduce the changed flow in a browser, not only in static code review.
- Check the browser console for errors and warnings.
- Check the network panel for failed asset requests.
- Confirm scene transitions, input, collisions, and camera behavior still work
  after restart or resize events.
